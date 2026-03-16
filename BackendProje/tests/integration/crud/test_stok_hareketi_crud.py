"""
Integration testler: StokHareketi CRUD — gerçek MySQL DB ile.
Gerçek CRUD fonksiyonlarını test eder (factory sadece ön veri için).
"""

import pytest
from schemas import StokHareketiCreate
from crud.stok_hareketi_crud import get_stok_hareketleri, create_stok_hareketi
from tests.factories import (
    UrunFactory,
    KullaniciFactory,
    LotFactory,
    PaletFactory,
    RafFactory,
)

pytestmark = pytest.mark.integration


class TestStokHareketiCrud:
    """StokHareketi CRUD integration testleri."""

    def test_create_stok_giris(self, db_session):
        """Stok giriş hareketi oluşturma — CRUD fonksiyonu üzerinden."""
        urun = UrunFactory.create()
        kullanici = KullaniciFactory.create()
        raf = RafFactory.create()

        dto = StokHareketiCreate(
            urun_id=urun.id,
            raf_id=raf.id,
            hareket_tipi="giris",
            miktar=50,
            aciklama="Test girişi",
        )

        hareket = create_stok_hareketi(db_session, dto, kullanici.id)

        assert hareket.id is not None
        assert hareket.hareket_tipi == "giris"
        assert hareket.miktar == 50
        assert hareket.urun_id == urun.id
        assert hareket.kullanici_id == kullanici.id

    def test_create_stok_cikis_fifo(self, db_session):
        """Stok çıkış hareketi — FIFO mantığıyla palet stoğu düşmeli."""
        urun = UrunFactory.create()
        kullanici = KullaniciFactory.create()
        lot = LotFactory.create(urun=urun)
        raf = RafFactory.create()
        palet = PaletFactory.create(lot=lot, raf=raf, koli_adedi=100)

        dto = StokHareketiCreate(
            urun_id=urun.id,
            hareket_tipi="cikis",
            miktar=30,
        )

        hareket = create_stok_hareketi(db_session, dto, kullanici.id)

        assert hareket.hareket_tipi == "cikis"
        assert hareket.miktar == 30

        # Palet stoğu düşmüş olmalı
        db_session.refresh(palet)
        assert palet.koli_adedi == 70

    def test_get_stok_hareketleri_filtre(self, db_session):
        """Hareket tipi filtresi ile listeleme."""
        urun = UrunFactory.create()
        kullanici = KullaniciFactory.create()
        raf = RafFactory.create()

        # Giriş hareketi
        create_stok_hareketi(db_session, StokHareketiCreate(
            urun_id=urun.id, raf_id=raf.id, hareket_tipi="giris", miktar=100,
        ), kullanici.id)

        result_giris = get_stok_hareketleri(db_session, hareket_tipi="giris")
        result_cikis = get_stok_hareketleri(db_session, hareket_tipi="cikis")

        assert len(result_giris) >= 1
        assert len(result_cikis) == 0

    def test_get_stok_hareketleri_urun_filtre(self, db_session):
        """Ürün ID filtresi ile listeleme."""
        urun1 = UrunFactory.create()
        urun2 = UrunFactory.create()
        kullanici = KullaniciFactory.create()
        raf = RafFactory.create()

        create_stok_hareketi(db_session, StokHareketiCreate(
            urun_id=urun1.id, raf_id=raf.id, hareket_tipi="giris", miktar=10,
        ), kullanici.id)
        create_stok_hareketi(db_session, StokHareketiCreate(
            urun_id=urun2.id, raf_id=raf.id, hareket_tipi="giris", miktar=20,
        ), kullanici.id)

        result = get_stok_hareketleri(db_session, urun_id=urun1.id)

        assert len(result) == 1
        assert result[0].urun_id == urun1.id
