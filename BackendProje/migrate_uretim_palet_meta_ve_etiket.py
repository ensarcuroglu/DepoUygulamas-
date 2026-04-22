"""
Migration: Üretim paleti meta alanları + Etiket şablonu modülü.

Değişiklikler:
  1. paletler tablosuna 5 yeni sütun (uretim_hatti, makine_kodu,
     operator_kullanici_id, brut_kg, net_kg)
  2. etiket_sablonlari tablosu (id, ad, boyut, zpl_template,
     html_template, default_mi, aktif, olusturan_id, olusturma_tarihi)
  3. palet_etiketleri tablosu (id, palet_id, sablon_id,
     render_edilmis_zpl, render_edilmis_html, barkod_deger, qr_deger,
     basim_sayisi, son_basim_tarihi, kullanici_id, olusturma_tarihi)

Çalıştırma:
    python migrate_uretim_palet_meta_ve_etiket.py
"""

import os
import sys

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(__file__))

from database import engine


# ── Yardımcı ──

def _sutun_var_mi(inspector, tablo: str, sutun: str) -> bool:
    mevcut = {col["name"] for col in inspector.get_columns(tablo)}
    return sutun in mevcut


def _tablo_var_mi(inspector, tablo: str) -> bool:
    return tablo in inspector.get_table_names()


def _is_sqlite() -> bool:
    return engine.dialect.name == "sqlite"


# ── Adım 1: paletler meta sütunları ──

PALET_META_SUTUNLARI = [
    ("uretim_hatti", "VARCHAR(50) NULL"),
    ("makine_kodu", "VARCHAR(50) NULL"),
    ("operator_kullanici_id", "INT NULL"),
    ("brut_kg", "FLOAT NULL"),
    ("net_kg", "FLOAT NULL"),
]


def _ekle_palet_meta_sutunlari(conn, inspector):
    for sutun_adi, sutun_tipi in PALET_META_SUTUNLARI:
        if _sutun_var_mi(inspector, "paletler", sutun_adi):
            print(f"  - paletler.{sutun_adi} zaten mevcut, atlandı.")
            continue
        # nosemgrep
        conn.execute(text(f"ALTER TABLE paletler ADD COLUMN {sutun_adi} {sutun_tipi}"))
        conn.commit()
        print(f"  ✓ paletler.{sutun_adi} eklendi.")

    if not _is_sqlite():
        try:
            conn.execute(text(
                "ALTER TABLE paletler ADD CONSTRAINT fk_paletler_operator "
                "FOREIGN KEY (operator_kullanici_id) REFERENCES kullanicilar(id)"
            ))
            conn.commit()
            print("  ✓ FK constraint fk_paletler_operator eklendi.")
        except Exception as e:
            print(f"  - FK constraint atlandı ({e}).")


# ── Adım 2: etiket_sablonlari ──

def _olustur_etiket_sablonlari(conn, inspector):
    if _tablo_var_mi(inspector, "etiket_sablonlari"):
        print("  - etiket_sablonlari tablosu zaten mevcut, atlandı.")
        return

    if _is_sqlite():
        ddl = """
        CREATE TABLE etiket_sablonlari (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ad VARCHAR(100) NOT NULL,
            boyut VARCHAR(30) NULL,
            zpl_template TEXT NOT NULL,
            html_template TEXT NOT NULL,
            default_mi BOOLEAN NOT NULL DEFAULT 0,
            aktif BOOLEAN NOT NULL DEFAULT 1,
            olusturan_id INTEGER NULL,
            olusturma_tarihi DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (olusturan_id) REFERENCES kullanicilar(id)
        )
        """
    else:
        ddl = """
        CREATE TABLE etiket_sablonlari (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ad VARCHAR(100) NOT NULL,
            boyut VARCHAR(30) NULL,
            zpl_template TEXT NOT NULL,
            html_template TEXT NOT NULL,
            default_mi BOOLEAN NOT NULL DEFAULT FALSE,
            aktif BOOLEAN NOT NULL DEFAULT TRUE,
            olusturan_id INT NULL,
            olusturma_tarihi DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_etiket_sablonu_olusturan
                FOREIGN KEY (olusturan_id) REFERENCES kullanicilar(id),
            INDEX idx_etiket_sablonlari_aktif (aktif),
            INDEX idx_etiket_sablonlari_default (default_mi)
        )
        """
    conn.execute(text(ddl))
    conn.commit()
    print("  ✓ etiket_sablonlari tablosu oluşturuldu.")


# ── Adım 3: palet_etiketleri ──

def _olustur_palet_etiketleri(conn, inspector):
    if _tablo_var_mi(inspector, "palet_etiketleri"):
        print("  - palet_etiketleri tablosu zaten mevcut, atlandı.")
        return

    if _is_sqlite():
        ddl = """
        CREATE TABLE palet_etiketleri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            palet_id INTEGER NOT NULL,
            sablon_id INTEGER NOT NULL,
            render_edilmis_zpl TEXT NOT NULL,
            render_edilmis_html TEXT NOT NULL,
            barkod_deger VARCHAR(100) NOT NULL,
            qr_deger VARCHAR(255) NULL,
            basim_sayisi INTEGER NOT NULL DEFAULT 0,
            son_basim_tarihi DATETIME NULL,
            kullanici_id INTEGER NULL,
            olusturma_tarihi DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (palet_id) REFERENCES paletler(id),
            FOREIGN KEY (sablon_id) REFERENCES etiket_sablonlari(id),
            FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id)
        )
        """
    else:
        ddl = """
        CREATE TABLE palet_etiketleri (
            id INT AUTO_INCREMENT PRIMARY KEY,
            palet_id INT NOT NULL,
            sablon_id INT NOT NULL,
            render_edilmis_zpl TEXT NOT NULL,
            render_edilmis_html TEXT NOT NULL,
            barkod_deger VARCHAR(100) NOT NULL,
            qr_deger VARCHAR(255) NULL,
            basim_sayisi INT NOT NULL DEFAULT 0,
            son_basim_tarihi DATETIME NULL,
            kullanici_id INT NULL,
            olusturma_tarihi DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_palet_etiket_palet FOREIGN KEY (palet_id) REFERENCES paletler(id),
            CONSTRAINT fk_palet_etiket_sablon FOREIGN KEY (sablon_id) REFERENCES etiket_sablonlari(id),
            CONSTRAINT fk_palet_etiket_kullanici FOREIGN KEY (kullanici_id) REFERENCES kullanicilar(id),
            INDEX idx_palet_etiketleri_palet (palet_id),
            INDEX idx_palet_etiketleri_sablon (sablon_id)
        )
        """
    conn.execute(text(ddl))
    conn.commit()
    print("  ✓ palet_etiketleri tablosu oluşturuldu.")


# ── Adım 4: default etiket şablonu seed ──

DEFAULT_ZPL = """^XA
^CF0,30
^FO20,20^FDURETIM PALETI^FS
^CF0,60
^FO20,60^FD{palet_no}^FS
^BY3,2,100
^FO20,130^BC^FD{barkod}^FS
^CF0,25
^FO20,250^FDUrun: {urun_isim}^FS
^FO20,280^FDLot: {lot_no}^FS
^FO20,310^FDSKT: {skt}^FS
^FO20,340^FDKoli: {koli} adet^FS
^FO20,370^FDVardiya: {vardiya}^FS
^XZ"""

DEFAULT_HTML = """<div style=\"font-family: sans-serif; border: 2px solid #000; padding: 16px; width: 400px;\">
  <h2 style=\"margin:0 0 8px\">ÜRETİM PALETİ</h2>
  <div style=\"font-size:22px;font-weight:700\">{palet_no}</div>
  <hr />
  <p><strong>Ürün:</strong> {urun_isim}</p>
  <p><strong>Lot:</strong> {lot_no}</p>
  <p><strong>SKT:</strong> {skt}</p>
  <p><strong>Koli:</strong> {koli} adet</p>
  <p><strong>Vardiya:</strong> {vardiya}</p>
  <p><strong>Üretim:</strong> {uretim_tarihi}</p>
</div>"""


def _seed_default_sablon(conn):
    mevcut = conn.execute(text("SELECT COUNT(*) FROM etiket_sablonlari")).scalar()
    if mevcut and mevcut > 0:
        print("  - Etiket şablonu zaten mevcut, seed atlandı.")
        return

    conn.execute(
        text(
            "INSERT INTO etiket_sablonlari "
            "(ad, boyut, zpl_template, html_template, default_mi, aktif, olusturan_id) "
            "VALUES (:ad, :boyut, :zpl, :html, :def_mi, :aktif, :olusturan)"
        ),
        {
            "ad": "Standart Üretim Paleti",
            "boyut": "100x150mm",
            "zpl": DEFAULT_ZPL,
            "html": DEFAULT_HTML,
            "def_mi": True,
            "aktif": True,
            "olusturan": None,
        },
    )
    conn.commit()
    print("  ✓ Varsayılan etiket şablonu eklendi.")


# ── Ana akış ──

def migrate():
    print("=== Üretim Paleti Meta + Etiket Modülü Migration ===\n")
    with engine.connect() as conn:
        inspector = inspect(conn)

        print("[1/4] paletler meta sütunları...")
        _ekle_palet_meta_sutunlari(conn, inspector)

        inspector = inspect(conn)
        print("\n[2/4] etiket_sablonlari tablosu...")
        _olustur_etiket_sablonlari(conn, inspector)

        inspector = inspect(conn)
        print("\n[3/4] palet_etiketleri tablosu...")
        _olustur_palet_etiketleri(conn, inspector)

        print("\n[4/4] Varsayılan etiket şablonu seed...")
        _seed_default_sablon(conn)

    print("\n=== Migration tamamlandı ===")


if __name__ == "__main__":
    migrate()
