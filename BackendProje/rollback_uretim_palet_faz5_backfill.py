"""
Rollback FAZ 5 — Üretim Paleti Veri Backfill Geri Alma.

paletler_faz5_backup snapshot tablosundan JOIN ile:
  • kaynak alanını orijinal değerine (NULL) döndürür
  • durum  alanını orijinal değerine (NULL) döndürür

Rollback SLA Hedefleri:
  • Seviye 1 (≤15dk): Feature flag kapatılır, backend yeniden başlatılır
  • Seviye 2 (≤30dk): Seviye 1 + bu script çalıştırılır

Kullanım:
    python rollback_uretim_palet_faz5_backfill.py [--dry-run] [--batch-size=1000]
"""

import argparse
import os
import sys
import time

from sqlalchemy import inspect, text

sys.path.insert(0, os.path.dirname(__file__))

from database import engine


def _tablo_var_mi(inspector, tablo: str) -> bool:
    return tablo in inspector.get_table_names()


def _onkosul_kontrol(inspector) -> None:
    if not _tablo_var_mi(inspector, "paletler_faz5_backup"):
        raise RuntimeError(
            "paletler_faz5_backup tablosu bulunamadı. "
            "Backfill hiç çalıştırılmamış veya backup silinmiş."
        )


def _rollback_batch(conn, batch_size: int, dry_run: bool) -> int:
    """Snapshot tablosundan JOIN ile orijinal değerlere döner (batch'li)."""
    if dry_run:
        etkilenecek = conn.execute(text("""
            SELECT COUNT(*)
            FROM paletler p
            JOIN paletler_faz5_backup b ON b.id = p.id
            WHERE (b.kaynak IS NULL AND p.kaynak IS NOT NULL)
               OR (b.durum  IS NULL AND p.durum  IS NOT NULL)
        """)).scalar()
        print(f"  [DRY-RUN] {etkilenecek} satır rollback edilecek.")
        return etkilenecek

    toplam = 0
    while True:
        sonuc = conn.execute(text(f"""
            UPDATE paletler p
            JOIN paletler_faz5_backup b ON b.id = p.id
            SET
                p.kaynak = b.kaynak,
                p.durum  = b.durum
            WHERE (b.kaynak IS NULL AND p.kaynak IS NOT NULL)
               OR (b.durum  IS NULL AND p.durum  IS NOT NULL)
            LIMIT {batch_size}
        """))
        conn.commit()
        etkilenen = sonuc.rowcount
        toplam += etkilenen
        if etkilenen == 0:
            break
        print(f"    batch: {etkilenen} satır geri alındı (toplam: {toplam})")

    return toplam


def _dogrula(conn) -> None:
    """Rollback sonrası snapshot ile tutarlılık kontrolü."""
    uyumsuz = conn.execute(text("""
        SELECT COUNT(*)
        FROM paletler p
        JOIN paletler_faz5_backup b ON b.id = p.id
        WHERE (b.kaynak IS NULL AND p.kaynak IS NOT NULL)
           OR (b.durum  IS NULL AND p.durum  IS NOT NULL)
    """)).scalar()

    if uyumsuz > 0:
        raise RuntimeError(f"Rollback doğrulaması başarısız: {uyumsuz} satır hâlâ uyumsuz.")

    print("\n✓ Rollback doğrulaması başarılı — snapshot ile tutarlı.")


def run(dry_run: bool = False, batch_size: int = 1000) -> None:
    mod = "[DRY-RUN] " if dry_run else ""
    print(f"Üretim Paleti FAZ 5 — Backfill Rollback {mod}")
    print("=" * 55)
    baslangic = time.time()

    inspector = inspect(engine)

    if not _tablo_var_mi(inspector, "paletler"):
        print("! paletler tablosu bulunamadı. İşlem atlandı.")
        return

    print("\n0. Ön koşul kontrolü (snapshot tablosu)...")
    _onkosul_kontrol(inspector)
    print("  ✓ paletler_faz5_backup mevcut.")

    with engine.connect() as conn:
        print(f"\n1. Rollback işlemi (batch={batch_size})...")
        toplam = _rollback_batch(conn, batch_size, dry_run)

        if not dry_run and toplam > 0:
            print("\n2. Doğrulama...")
            _dogrula(conn)
        elif toplam == 0:
            print("  ✓ Rollback edilecek satır yok.")

    sure = time.time() - baslangic
    print(f"\n{'✓' if not dry_run else '[DRY-RUN]'} Rollback tamamlandı — "
          f"{toplam} satır ({sure:.1f}s)")
    print("\n[!] Seviye 1 rollback için feature flag'i de kapatmayı unutmayın:")
    print("    FEATURE_URETIM_PALET_PILOT_DEPO_IDS=  (boş bırak)")
    print("    VITE_FEATURE_URETIM_PALET_ENABLED=false")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Üretim paleti FAZ 5 backfill rollback")
    parser.add_argument("--dry-run", action="store_true", help="Etki analizi yap, değişiklik yapma")
    parser.add_argument("--batch-size", type=int, default=1000, help="Batch boyutu (varsayılan: 1000)")
    args = parser.parse_args()
    run(dry_run=args.dry_run, batch_size=args.batch_size)
