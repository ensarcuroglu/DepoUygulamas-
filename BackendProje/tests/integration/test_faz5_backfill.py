"""Integration testleri — FAZ 5 Backfill ve Rollback scriptleri.

Test DB üzerinde legacy palet satırları oluşturulur, backfill çalıştırılır,
doğrulama yapılır; ardından rollback ile orijinal state'e dönülür.
"""

import pytest
from sqlalchemy import text, inspect


pytestmark = pytest.mark.integration


def _setup_test_data(conn, prefix: str) -> tuple[int, int]:
    """
    Her test için bağımsız ve zorunlu alanları eksiksiz temel veri hiyerarşisini kurar.
    Geriye, palet oluşturmak için gereken (lot_id, raf_id) ikilisini döner.
    """
    marka_id = conn.execute(text(
        "INSERT INTO markalar (isim, aktif) VALUES (:isim, 1)"
    ), {"isim": f"{prefix}_Marka"}).lastrowid

    kategori_id = conn.execute(text(
        "INSERT INTO kategoriler (isim, aciklama, ikon, aktif) VALUES (:isim, '', '', 1)"
    ), {"isim": f"{prefix}_Kat"}).lastrowid

    urun_id = conn.execute(text(
        "INSERT INTO urunler (isim, marka_id, kategori_id, barkod, birim, fiyat, min_stok, aktif, ic_adet, aciklama, depolama_tipi) "
        "VALUES (:isim, :m, :k, :barkod, 'Adet', 10, 5, 1, 1, '', 'Kuru')"
    ), {"isim": f"{prefix}_Urun", "m": marka_id, "k": kategori_id, "barkod": f"BC-{prefix}"}).lastrowid

    lot_id = conn.execute(text(
        "INSERT INTO lotlar (urun_id, lot_no, aciklama, aktif) VALUES (:u, :lot_no, '', 1)"
    ), {"u": urun_id, "lot_no": f"LOT-{prefix}"}).lastrowid

    depo_id = conn.execute(text(
        "INSERT INTO depolar (isim, adres, aciklama, aktif) VALUES (:isim, 'Test Adresi', '', 1)"
    ), {"isim": f"{prefix}_Depo"}).lastrowid

    raf_id = conn.execute(text(
        "INSERT INTO raflar (depo_id, kod, bolge, koridor, kapasite, aktif, kat, goz, is_staging) "
        "VALUES (:d, :kod, 'TestBolge', '', 100, 1, 0, 0, 0)"
    ), {"d": depo_id, "kod": f"RAF-{prefix}"}).lastrowid

    conn.commit()
    return lot_id, raf_id


def _insert_legacy_palet(conn, lot_id: int, raf_id: int, palet_no: str, aktif: int = 1):
    """kaynak=NULL, durum=NULL legacy palet satırı ekler."""
    conn.execute(text("""
        INSERT INTO paletler (lot_id, raf_id, palet_no, koli_adedi, aktif,
                              kaynak, durum, olusturma_tarihi)
        VALUES (:lot_id, :raf_id, :palet_no, 10, :aktif, NULL, NULL, NOW())
    """), {"lot_id": lot_id, "raf_id": raf_id, "palet_no": palet_no, "aktif": aktif})
    conn.commit()


def _insert_modern_palet(conn, lot_id: int, raf_id: int, palet_no: str):
    """kaynak ve durum dolu modern palet satırı ekler (backfill'den etkilenmemeli)."""
    conn.execute(text("""
        INSERT INTO paletler (lot_id, raf_id, palet_no, koli_adedi, aktif,
                              kaynak, durum, olusturma_tarihi)
        VALUES (:lot_id, :raf_id, :palet_no, 10, 1, 'uretim', 'KABUL_EDILDI', NOW())
    """), {"lot_id": lot_id, "raf_id": raf_id, "palet_no": palet_no})
    conn.commit()


def _cleanup_backup(conn):
    """Her test öncesi/sonrası yedek tablosunu temizler."""
    try:
        conn.execute(text("DROP TABLE IF EXISTS paletler_faz5_backup"))
        conn.commit()
    except Exception:
        pass


class TestFaz5Backfill:

    def test_backfill_legacy_aktif_palet(self, engine, db_session):
        """aktif=1, kaynak=NULL, durum=NULL → kaynak='irsaliye', durum='YERLESTIRILDI'."""
        from migrate_uretim_palet_faz5_backfill import run as backfill_run

        with engine.connect() as conn:
            _cleanup_backup(conn)
            
            # Helper fonksiyonu ile temiz ve tek satırda veri oluşturumu
            lot_id, raf_id = _setup_test_data(conn, prefix="BF_Aktif")

            _insert_legacy_palet(conn, lot_id, raf_id, "PLT-LEGACY-AKTIF", aktif=1)
            _insert_modern_palet(conn, lot_id, raf_id, "PRD-MODERN-001")

        backfill_run(dry_run=False, batch_size=500)

        with engine.connect() as conn:
            # Legacy palet değişmiş olmalı
            row = conn.execute(text(
                "SELECT kaynak, durum FROM paletler WHERE palet_no = 'PLT-LEGACY-AKTIF'"
            )).fetchone()
            assert row is not None
            assert row[0] == "irsaliye"
            assert row[1] == "YERLESTIRILDI"

            # Modern palet değişmemiş olmalı
            modern = conn.execute(text(
                "SELECT kaynak, durum FROM paletler WHERE palet_no = 'PRD-MODERN-001'"
            )).fetchone()
            assert modern[0] == "uretim"
            assert modern[1] == "KABUL_EDILDI"

            _cleanup_backup(conn)

    def test_backfill_legacy_pasif_palet(self, engine, db_session):
        """aktif=0, kaynak=NULL, durum=NULL → durum='IPTAL_EDILDI'."""
        from migrate_uretim_palet_faz5_backfill import run as backfill_run

        with engine.connect() as conn:
            _cleanup_backup(conn)
            
            lot_id, raf_id = _setup_test_data(conn, prefix="BF_Pasif")
            _insert_legacy_palet(conn, lot_id, raf_id, "PLT-LEGACY-PASIF", aktif=0)

        backfill_run(dry_run=False, batch_size=500)

        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT kaynak, durum FROM paletler WHERE palet_no = 'PLT-LEGACY-PASIF'"
            )).fetchone()
            assert row[0] == "irsaliye"
            assert row[1] == "IPTAL_EDILDI"
            
            _cleanup_backup(conn)

    def test_backfill_dry_run_degisiklik_yapmaz(self, engine, db_session):
        """--dry-run modunda hiçbir şey değişmemeli."""
        from migrate_uretim_palet_faz5_backfill import run as backfill_run

        with engine.connect() as conn:
            _cleanup_backup(conn)

        backfill_run(dry_run=True, batch_size=1000)

        with engine.connect() as conn:
            backup_var = "paletler_faz5_backup" in inspect(engine).get_table_names()
            assert not backup_var, "dry-run'da backup tablosu oluşmamalı"
            _cleanup_backup(conn)

    def test_backfill_idempotent(self, engine, db_session):
        """İki kez çalıştırıldığında hata vermemeli, değerler değişmemeli."""
        from migrate_uretim_palet_faz5_backfill import run as backfill_run

        with engine.connect() as conn:
            _cleanup_backup(conn)

        # İlk çalıştırma
        backfill_run(dry_run=False, batch_size=1000)
        
        # İkinci çalıştırma (idempotency kontrolü)
        backfill_run(dry_run=False, batch_size=1000)

        with engine.connect() as conn:
            _cleanup_backup(conn)

    def test_rollback_snapshot_geri_yuklenir(self, engine, db_session):
        """Backfill sonrası rollback script orijinal NULL değerlerine döner."""
        from migrate_uretim_palet_faz5_backfill import run as backfill_run
        from rollback_uretim_palet_faz5_backfill import run as rollback_run

        with engine.connect() as conn:
            _cleanup_backup(conn)
            
            lot_id, raf_id = _setup_test_data(conn, prefix="RB_Test")
            _insert_legacy_palet(conn, lot_id, raf_id, "PLT-ROLLBACK-001", aktif=1)

        # Backfill çalıştır ve doğrula
        backfill_run(dry_run=False, batch_size=500)

        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT kaynak, durum FROM paletler WHERE palet_no = 'PLT-ROLLBACK-001'"
            )).fetchone()
            assert row[0] == "irsaliye"

        # Rollback çalıştır ve orjinal state'e dönüldüğünü doğrula
        rollback_run(dry_run=False, batch_size=500)

        with engine.connect() as conn:
            row = conn.execute(text(
                "SELECT kaynak, durum FROM paletler WHERE palet_no = 'PLT-ROLLBACK-001'"
            )).fetchone()
            assert row[0] is None
            assert row[1] is None

            _cleanup_backup(conn)