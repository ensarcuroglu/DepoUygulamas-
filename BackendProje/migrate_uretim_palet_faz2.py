"""
Migration: Üretim paleti desteği — FAZ 2 veri modeli.

Değişiklikler:
  1. paletler tablosuna 7 yeni sütun
  2. paletler.durum sütununa index
  3. uretim_seri_sayac tablosu
  4. palet_durum_log tablosu

Çalıştırma:
    python migrate_uretim_palet_faz2.py
"""

import os
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(__file__))

from database import engine


# ── Yardımcı fonksiyonlar ──

def _sutun_var_mi(inspector, tablo: str, sutun: str) -> bool:
    mevcut = {col["name"] for col in inspector.get_columns(tablo)}
    return sutun in mevcut


def _tablo_var_mi(inspector, tablo: str) -> bool:
    return tablo in inspector.get_table_names()


def _index_var_mi(inspector, tablo: str, index_adi: str) -> bool:
    indexes = {idx["name"] for idx in inspector.get_indexes(tablo) if idx.get("name")}
    return index_adi in indexes


def _is_sqlite() -> bool:
    return engine.dialect.name == "sqlite"


# ── Adım 1: paletler tablosuna yeni sütunlar ──

PALET_SUTUNLARI = [
    ("kaynak", "VARCHAR(20) NULL"),
    ("durum", "VARCHAR(30) NULL"),
    ("uretim_tarihi", "DATE NULL" if not _is_sqlite() else "DATE"),
    ("lot_no", "VARCHAR(30) NULL"),
    ("kabul_eden_kullanici_id", "INT NULL"),
    ("kabul_tarihi", "DATETIME NULL" if not _is_sqlite() else "DATETIME"),
    ("iptal_sebebi", "VARCHAR(255) NULL"),
]


def _ekle_palet_sutunlari(conn, inspector):
    """paletler tablosuna 7 yeni sütun ekler (idempotent)."""
    for sutun_adi, sutun_tipi in PALET_SUTUNLARI:
        if _sutun_var_mi(inspector, "paletler", sutun_adi):
            print(f"  - paletler.{sutun_adi} zaten mevcut, atlandı.")
            continue
        # nosemgrep
        conn.execute(text(
            f"ALTER TABLE paletler ADD COLUMN {sutun_adi} {sutun_tipi}"
        ))
        conn.commit()
        print(f"  ✓ paletler.{sutun_adi} eklendi.")

    # FK constraint — sadece MySQL
    if not _is_sqlite():
        try:
            conn.execute(text(
                "ALTER TABLE paletler ADD CONSTRAINT fk_paletler_kabul_eden "
                "FOREIGN KEY (kabul_eden_kullanici_id) REFERENCES kullanicilar(id)"
            ))
            conn.commit()
            print("  ✓ FK constraint fk_paletler_kabul_eden eklendi.")
        except Exception:
            # FK zaten varsa veya başka bir sebeple eklenemezse devam et
            conn.rollback()
            print("  - FK constraint fk_paletler_kabul_eden zaten mevcut veya atlandı.")


# ── Adım 2: durum index ──

DURUM_INDEX = "ix_paletler_durum"


def _ekle_durum_index(conn, inspector):
    """paletler.durum sütununa index ekler (idempotent)."""
    if _index_var_mi(inspector, "paletler", DURUM_INDEX):
        print(f"  - {DURUM_INDEX} zaten mevcut, atlandı.")
        return
    conn.execute(text(f"CREATE INDEX {DURUM_INDEX} ON paletler(durum)"))
    conn.commit()
    print(f"  ✓ {DURUM_INDEX} oluşturuldu.")


# ── Adım 3: uretim_seri_sayac tablosu ──

def _olustur_seri_sayac(conn, inspector):
    """uretim_seri_sayac tablosunu oluşturur (idempotent)."""
    if _tablo_var_mi(inspector, "uretim_seri_sayac"):
        print("  - uretim_seri_sayac tablosu zaten mevcut, atlandı.")
        return

    if _is_sqlite():
        sql = """
        CREATE TABLE uretim_seri_sayac (
            tarih DATE NOT NULL PRIMARY KEY,
            son_seri_no INTEGER NOT NULL DEFAULT 0
        )
        """
    else:
        sql = """
        CREATE TABLE uretim_seri_sayac (
            tarih DATE NOT NULL PRIMARY KEY,
            son_seri_no INT NOT NULL DEFAULT 0
        )
        """

    conn.execute(text(sql))
    conn.commit()
    print("  ✓ uretim_seri_sayac tablosu oluşturuldu.")


# ── Adım 4: palet_durum_log tablosu ──

def _olustur_durum_log(conn, inspector):
    """palet_durum_log tablosunu oluşturur (idempotent)."""
    if _tablo_var_mi(inspector, "palet_durum_log"):
        print("  - palet_durum_log tablosu zaten mevcut, atlandı.")
        return

    if _is_sqlite():
        sql = """
        CREATE TABLE palet_durum_log (
            id INTEGER NOT NULL PRIMARY KEY,
            palet_id INTEGER NOT NULL REFERENCES paletler(id),
            eski_durum VARCHAR(30),
            yeni_durum VARCHAR(30) NOT NULL,
            degistiren_kullanici_id INTEGER REFERENCES kullanicilar(id),
            degisim_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            sebep VARCHAR(255)
        )
        """
    else:
        sql = """
        CREATE TABLE palet_durum_log (
            id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
            palet_id INT NOT NULL,
            eski_durum VARCHAR(30) NULL,
            yeni_durum VARCHAR(30) NOT NULL,
            degistiren_kullanici_id INT NULL,
            degisim_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP,
            sebep VARCHAR(255) NULL,
            CONSTRAINT fk_palet_durum_log_palet
                FOREIGN KEY (palet_id) REFERENCES paletler(id),
            CONSTRAINT fk_palet_durum_log_kullanici
                FOREIGN KEY (degistiren_kullanici_id) REFERENCES kullanicilar(id)
        )
        """

    conn.execute(text(sql))
    conn.commit()
    print("  ✓ palet_durum_log tablosu oluşturuldu.")


# ── Doğrulama ──

def _dogrula(inspector):
    """Migration sonrası doğrulama."""
    hatalar = []

    # Sütun kontrolü
    for sutun_adi, _ in PALET_SUTUNLARI:
        if not _sutun_var_mi(inspector, "paletler", sutun_adi):
            hatalar.append(f"paletler.{sutun_adi} bulunamadı")

    # Tablo kontrolü
    for tablo in ("uretim_seri_sayac", "palet_durum_log"):
        if not _tablo_var_mi(inspector, tablo):
            hatalar.append(f"{tablo} tablosu bulunamadı")

    if hatalar:
        raise RuntimeError(
            "Migration doğrulaması başarısız:\n  " + "\n  ".join(hatalar)
        )

    print("\n✓ Tüm doğrulamalar başarılı.")


# ── Ana fonksiyon ──

def run():
    print("Üretim Paleti FAZ 2 — Veri Modeli Migration")
    print("=" * 50)

    inspector = inspect(engine)

    if not _tablo_var_mi(inspector, "paletler"):
        print("! paletler tablosu bulunamadı. Migration atlandı.")
        return

    with engine.connect() as conn:
        print("\n1. Paletler tablosuna yeni sütunlar ekleniyor...")
        _ekle_palet_sutunlari(conn, inspector)

        # Inspector'ı yenile (yeni sütunlar eklendi)
        inspector = inspect(engine)

        print("\n2. Durum index oluşturuluyor...")
        _ekle_durum_index(conn, inspector)

        print("\n3. Üretim seri sayaç tablosu oluşturuluyor...")
        _olustur_seri_sayac(conn, inspector)

        print("\n4. Palet durum log tablosu oluşturuluyor...")
        _olustur_durum_log(conn, inspector)

    # Doğrulama (yeni bağlantı ile)
    print("\n5. Doğrulama...")
    _dogrula(inspect(engine))


if __name__ == "__main__":
    run()
