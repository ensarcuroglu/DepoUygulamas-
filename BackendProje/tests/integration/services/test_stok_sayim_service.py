"""Integration testler: StokSayimService — gerçek MySQL DB ile.

Not: Service katmanı DB bağımlı olduğu için unit değil integration test olarak çalışır.
Dosya konumu unit/ altında ancak marker integration'dır.
"""

import pytest
from services.stok_sayim_service import StokSayimService
from schemas import StokSayimCreate, StokSayimKalemiCreate
from core.exceptions import NotFoundError, BadRequestError
from tests.factories import (
    KullaniciFactory,
    UrunFactory,
    LotFactory,
    PaletFactory,
    StokSayimFactory,
)

pytestmark = pytest.mark.integration


class TestStokSayimService:

    def test_basla(self, db_session):
        """Yeni sayım başlatma + referans stok snapshot."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        lot = LotFactory.create(urun=urun)
        PaletFactory.create(lot=lot, koli_adedi=50)

        dto = StokSayimCreate(aciklama="Test sayimi")
        sayim = StokSayimService.basla(db_session, dto, kullanici.id)

        assert sayim.id is not None
        assert sayim.sayim_no.startswith("SAY-")
        assert sayim.durum == "devam_ediyor"
        assert str(urun.id) in sayim.referans_stok_json
        assert sayim.referans_stok_json[str(urun.id)] == 50

    def test_basla_bos_stok(self, db_session):
        """Stok yokken de sayım başlatılabilmeli."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()

        dto = StokSayimCreate(aciklama="Bos stok sayimi")
        sayim = StokSayimService.basla(db_session, dto, kullanici.id)

        assert sayim.referans_stok_json[str(urun.id)] == 0

    def test_kalem_kaydet_yeni(self, db_session):
        """Yeni ürün kaydı (insert)."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="devam_ediyor",
        )

        dto = StokSayimKalemiCreate(urun_id=urun.id, sayilan_miktar=42)
        kalem = StokSayimService.kalem_kaydet(db_session, sayim.id, dto, kullanici.id)

        assert kalem.sayilan_miktar == 42
        assert kalem.urun_id == urun.id

    def test_kalem_kaydet_upsert(self, db_session):
        """Aynı ürün tekrar tarandığında miktar güncellenmeli (upsert)."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="devam_ediyor",
        )

        dto1 = StokSayimKalemiCreate(urun_id=urun.id, sayilan_miktar=10)
        StokSayimService.kalem_kaydet(db_session, sayim.id, dto1, kullanici.id)

        dto2 = StokSayimKalemiCreate(urun_id=urun.id, sayilan_miktar=25)
        kalem = StokSayimService.kalem_kaydet(db_session, sayim.id, dto2, kullanici.id)

        assert kalem.sayilan_miktar == 25

    def test_kalem_kaydet_sayim_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        dto = StokSayimKalemiCreate(urun_id=urun.id, sayilan_miktar=5)

        with pytest.raises(NotFoundError):
            StokSayimService.kalem_kaydet(db_session, 99999, dto, kullanici.id)

    def test_kalem_kaydet_sayim_kapali(self, db_session):
        """Onaylanmış sayıma kalem eklenemez."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="onaylandı",
        )

        dto = StokSayimKalemiCreate(urun_id=urun.id, sayilan_miktar=5)

        with pytest.raises(BadRequestError):
            StokSayimService.kalem_kaydet(db_session, sayim.id, dto, kullanici.id)

    def test_kalem_kaydet_urun_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="devam_ediyor",
        )

        dto = StokSayimKalemiCreate(urun_id=99999, sayilan_miktar=5)

        with pytest.raises(NotFoundError):
            StokSayimService.kalem_kaydet(db_session, sayim.id, dto, kullanici.id)

    def test_varyans_hesapla_sapma_var(self, db_session):
        """Referans ile sayılan arasında fark varsa varyans dönmeli."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="devam_ediyor",
            referans_stok_json={str(urun.id): 100},
        )

        # 80 sayıldı, beklenen 100 → fark -20
        dto = StokSayimKalemiCreate(urun_id=urun.id, sayilan_miktar=80)
        StokSayimService.kalem_kaydet(db_session, sayim.id, dto, kullanici.id)

        result = StokSayimService.varyans_hesapla(db_session, sayim.id)

        assert result["sayim_no"] == sayim.sayim_no
        assert len(result["varyanslar"]) == 1
        varyans = result["varyanslar"][0]
        assert varyans["beklenen"] == 100
        assert varyans["sayilan"] == 80
        assert varyans["fark"] == -20
        assert varyans["yuzde"] == -20.0
        assert result["toplam_sapma"] == 20

    def test_varyans_hesapla_sapma_yok(self, db_session):
        """Sayılan = referans ise varyans boş olmalı."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="devam_ediyor",
            referans_stok_json={str(urun.id): 50},
        )

        dto = StokSayimKalemiCreate(urun_id=urun.id, sayilan_miktar=50)
        StokSayimService.kalem_kaydet(db_session, sayim.id, dto, kullanici.id)

        result = StokSayimService.varyans_hesapla(db_session, sayim.id)

        assert len(result["varyanslar"]) == 0
        assert result["toplam_sapma"] == 0

    def test_varyans_hesapla_sayim_bulunamadi(self, db_session):
        with pytest.raises(NotFoundError):
            StokSayimService.varyans_hesapla(db_session, 99999)

    def test_onayla(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="devam_ediyor",
        )

        result = StokSayimService.onayla(db_session, sayim.id, kullanici.id)

        assert result["message"] == "Sayım onaylandı"
        assert result["sayim_no"] == sayim.sayim_no

        # DB'deki durum kontrol
        db_session.refresh(sayim)
        assert sayim.durum == "onaylandı"
        assert sayim.bitis_tarihi is not None
        assert sayim.onaylayan_user_id == kullanici.id

    def test_onayla_zaten_onayli(self, db_session):
        """Zaten onaylanmış sayım tekrar onaylanamaz."""
        kullanici = KullaniciFactory.create(rol="admin")
        sayim = StokSayimFactory.create(
            kontrol_eden=kullanici,
            durum="onaylandı",
        )

        with pytest.raises(BadRequestError):
            StokSayimService.onayla(db_session, sayim.id, kullanici.id)

    def test_onayla_sayim_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")

        with pytest.raises(NotFoundError):
            StokSayimService.onayla(db_session, 99999, kullanici.id)

    def test_get_sayimlar(self, db_session):
        StokSayimFactory.create()
        StokSayimFactory.create()
        StokSayimFactory.create(aktif=False)

        result = StokSayimService.get_sayimlar(db_session)

        assert len(result) == 2

    def test_get_sayim(self, db_session):
        sayim = StokSayimFactory.create()

        result = StokSayimService.get_sayim(db_session, sayim.id)

        assert result.id == sayim.id

    def test_get_sayim_bulunamadi(self, db_session):
        with pytest.raises(NotFoundError):
            StokSayimService.get_sayim(db_session, 99999)
