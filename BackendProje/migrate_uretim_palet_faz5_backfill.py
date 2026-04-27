"""
Migration FAZ 5 — Üretim Paleti Veri Backfill.

Mevcut paletlere canonical model alanları atar:
  • kaynak IS NULL  → 'irsaliye'
  • durum  IS NULL  → 'YERLESTIRILDI' (aktif=1) / 'IPTAL_EDILDI' (aktif=0)

Güvenlik:
  • Batch işlem (varsayılan 1000 kayıt/batch) — büyük tablolarda kilit minimizasyonu
  • --dry-run flag ile önce etki analizi yapılabilir
  • Çalıştırma öncesi paletler_faz5_backup snapshot tablosu oluşturulur
  • Idempotent: tekrar çalıştırılabilir, zaten dolu alanlar atlanır

Kullanım:
    python migrate_uretim_palet_faz5_backfill.py [--dry-run] [--batch-size=1000]
"""

import argparse
import os
import sys
import time

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(__file__))

from database import engine


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcılar
# ─────────────────────────────────────────────────────────────────────────────

def _tablo_var_mi(inspector, tablo: str) -> bool:
    return tablo in inspector.get_table_names()


def _sutun_var_mi(inspector, tablo: str, sutun: str) -> bool:
    return sutun in {c["name"] for c in inspector.get_columns(tablo)}


# ─────────────────────────────────────────────────────────────────────────────
# Adım 0: Ön koşul kontrolü
# ─────────────────────────────────────────────────────────────────────────────

def _onkosul_kontrol(inspector) -> None:
    """FAZ 2 migration'ının tamamlandığını doğrular."""
    eksik = []
    for sutun in ("kaynak", "durum", "uretim_tarihi", "lot_no",
                  "kabul_eden_kullanici_id", "kabul_tarihi", "iptal_sebebi"):
        if not _sutun_var_mi(inspector, "paletler", sutun):
            eksik.append(f"paletler.{sutun}")
    if eksik:
        raise RuntimeError(
            "FAZ 2 migration tamamlanmamış. Eksik sütunlar:\n  " + "\n  ".join(eksik) +
            "\n\nÖnce migrate_uretim_palet_faz2.py çalıştırın."
        )


# ─────────────────────────────────────────────────────────────────────────────
# Adım 1: Snapshot oluştur
# ─────────────────────────────────────────────────────────────────────────────

def _snapshot_olustur(conn, inspector, dry_run: bool) -> int:
    """Mevcut kaynak/durum değerlerini yedekler. Sadece NULL olan satırları alır."""
    if dry_run:
        sonuc = conn.execute(text(
            "SELECT COUNT(*) FROM paletler WHERE kaynak IS NULL OR durum IS NULL"
        )).scalar()
        print(f"  [DRY-RUN] {sonuc} satır backfill edilecek.")
        return sonuc

    if _tablo_var_mi(inspector, "paletler_faz5_backup"):
        print("  - paletler_faz5_backup zaten mevcut, yeniden oluşturulmadı.")
    else:
        conn.execute(text("""
            CREATE TABLE paletler_faz5_backup AS
            SELECT id, kaynak, durum, aktif
            FROM paletler
            WHERE kaynak IS NULL OR durum IS NULL
        """))
        conn.commit()
        sayim = conn.execute(text("SELECT COUNT(*) FROM paletler_faz5_backup")).scalar()
        print(f"  ✓ Snapshot oluşturuldu: {sayim} satır → paletler_faz5_backup")
        return sayim

    sayim = conn.execute(text("SELECT COUNT(*) FROM paletler_faz5_backup")).scalar()
    return sayim


# ─────────────────────────────────────────────────────────────────────────────
# Adım 2: Kaynak backfill
# ─────────────────────────────────────────────────────────────────────────────

def _backfill_kaynak(conn, batch_size: int, dry_run: bool) -> int:
    """kaynak IS NULL → 'irsaliye' (batch'li)."""
    toplam = 0
    while True:
        if dry_run:
            etkilenen = conn.execute(text(
                "SELECT COUNT(*) FROM paletler WHERE kaynak IS NULL"
            )).scalar()
            print(f"  [DRY-RUN] kaynak: {etkilenen} satır güncellenecek.")
            return etkilenen

        sonuc = conn.execute(text(
            f"UPDATE paletler SET kaynak = 'irsaliye' "
            f"WHERE kaynak IS NULL LIMIT {batch_size}"
        ))
        conn.commit()
        etkilenen = sonuc.rowcount
        toplam += etkilenen
        if etkilenen == 0:
            break
        print(f"    batch: {etkilenen} satır kaynak='irsaliye' yapıldı (toplam: {toplam})")

    return toplam


# ─────────────────────────────────────────────────────────────────────────────
# Adım 3: Durum backfill
# ─────────────────────────────────────────────────────────────────────────────

def _backfill_durum(conn, batch_size: int, dry_run: bool) -> int:
    """durum IS NULL → aktif=1 → 'YERLESTIRILDI', aktif=0 → 'IPTAL_EDILDI' (batch'li)."""
    if dry_run:
        aktif = conn.execute(text(
            "SELECT COUNT(*) FROM paletler WHERE durum IS NULL AND aktif = 1"
        )).scalar()
        pasif = conn.execute(text(
            "SELECT COUNT(*) FROM paletler WHERE durum IS NULL AND aktif = 0"
        )).scalar()
        print(f"  [DRY-RUN] durum: {aktif} satır YERLESTIRILDI, {pasif} satır IPTAL_EDILDI yapılacak.")
        return aktif + pasif

    toplam = 0
    # aktif = 1 → YERLESTIRILDI
    while True:
        sonuc = conn.execute(text(
            f"UPDATE paletler SET durum = 'YERLESTIRILDI' "
            f"WHERE durum IS NULL AND aktif = 1 LIMIT {batch_size}"
        ))
        conn.commit()
        etkilenen = sonuc.rowcount
        toplam += etkilenen
        if etkilenen == 0:
            break
        print(f"    batch: {etkilenen} satır durum='YERLESTIRILDI' yapıldı (toplam: {toplam})")

    # aktif = 0 → IPTAL_EDILDI
    while True:
        sonuc = conn.execute(text(
            f"UPDATE paletler SET durum = 'IPTAL_EDILDI' "
            f"WHERE durum IS NULL AND aktif = 0 LIMIT {batch_size}"
        ))
        conn.commit()
        etkilenen = sonuc.rowcount
        toplam += etkilenen
        if etkilenen == 0:
            break
        print(f"    batch: {etkilenen} satır durum='IPTAL_EDILDI' yapıldı (toplam: {toplam})")

    return toplam


# ─────────────────────────────────────────────────────────────────────────────
# Adım 4: Doğrulama
# ─────────────────────────────────────────────────────────────────────────────

def _dogrula(conn) -> None:
    kaynak_null = conn.execute(text(
        "SELECT COUNT(*) FROM paletler WHERE kaynak IS NULL"
    )).scalar()
    durum_null = conn.execute(text(
        "SELECT COUNT(*) FROM paletler WHERE durum IS NULL"
    )).scalar()

    hatalar = []
    if kaynak_null > 0:
        hatalar.append(f"paletler.kaynak hâlâ NULL: {kaynak_null} satır")
    if durum_null > 0:
        hatalar.append(f"paletler.durum hâlâ NULL: {durum_null} satır")

    if hatalar:
        raise RuntimeError("Doğrulama başarısız:\n  " + "\n  ".join(hatalar))

    toplam = conn.execute(text("SELECT COUNT(*) FROM paletler")).scalar()
    print(f"\n✓ Doğrulama başarılı — toplam {toplam} palet, NULL kaynak/durum yok.")


# ─────────────────────────────────────────────────────────────────────────────
# Ana fonksiyon
# ─────────────────────────────────────────────────────────────────────────────

def run(dry_run: bool = False, batch_size: int = 1000) -> None:
    mod = "[DRY-RUN] " if dry_run else ""
    print(f"Üretim Paleti FAZ 5 — Veri Backfill {mod}")
    print("=" * 55)
    baslangic = time.time()

    inspector = inspect(engine)

    if not _tablo_var_mi(inspector, "paletler"):
        print("! paletler tablosu bulunamadı. İşlem atlandı.")
        return

    print("\n0. Ön koşul kontrolü...")
    _onkosul_kontrol(inspector)
    print("  ✓ FAZ 2 migration doğrulandı.")

    with engine.connect() as conn:
        print("\n1. Snapshot oluşturuluyor (kaynak/durum NULL satırlar)...")
        snapshot_sayisi = _snapshot_olustur(conn, inspector, dry_run)

        if snapshot_sayisi == 0:
            print("  ✓ Backfill'e gerek yok — tüm alanlar dolu.")
            return

        print(f"\n2. kaynak backfill (batch={batch_size})...")
        kaynak_toplam = _backfill_kaynak(conn, batch_size, dry_run)

        print(f"\n3. durum backfill (batch={batch_size})...")
        durum_toplam = _backfill_durum(conn, batch_size, dry_run)

        if not dry_run:
            print("\n4. Doğrulama...")
            _dogrula(conn)

    sure = time.time() - baslangic
    print(f"\n{'✓' if not dry_run else '[DRY-RUN]'} Tamamlandı — "
          f"kaynak: {kaynak_toplam}, durum: {durum_toplam} satır "
          f"({sure:.1f}s)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Üretim paleti FAZ 5 backfill")
    parser.add_argument("--dry-run", action="store_true", help="Etki analizi yap, değişiklik yapma")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch boyutu (varsayılan: 1000)")
    args = parser.parse_args()
    run(dry_run=args.dry_run, batch_size=args.batch_size)
