"""Integration testler: Sevkiyat CRUD — gerçek MySQL DB ile."""

import pytest
from datetime import date, timedelta
from crud.sevkiyat_crud import (
    get_sevkiyat_planlari,
    get_sevkiyat_plani,
    create_sevkiyat_plani,
    update_sevkiyat_plani,
    delete_sevkiyat_plani,
)
from schemas import SevkiyatPlaniCreate, SevkiyatPlaniUpdate
from models import SistemLog, StokHareketi
from tests.factories import (
    SiparisFactory,
    SiparisKalemiFactory,
    SevkiyatPlaniFactory,
    KullaniciFactory,
    UrunFactory,
    LotFactory,
    PaletFactory,
)

pytestmark = pytest.mark.integration


class TestSevkiyatCrud:

    def test_create_sevkiyat_plani(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        siparis = SiparisFactory.create()

        dto = SevkiyatPlaniCreate(
            siparis_id=siparis.id,
            yukleme_tarihi=date.today() + timedelta(days=1),
            tir_plaka="34 ABC 001",
            sofor_adi="Ali Yilmaz",
            depo_kapi="Kapi-2",
        )

        result = create_sevkiyat_plani(db_session, dto, kullanici.id)

        assert result.id is not None
        assert result.siparis_id == siparis.id
        assert result.durum == "Planlandi"
        assert result.tir_plaka == "34 ABC 001"

    def test_create_sevkiyat_sistem_log(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        siparis = SiparisFactory.create()

        dto = SevkiyatPlaniCreate(
            siparis_id=siparis.id,
            yukleme_tarihi=date.today() + timedelta(days=1),
        )
        create_sevkiyat_plani(db_session, dto, kullanici.id)

        log = db_session.query(SistemLog).filter(
            SistemLog.modul == "Sevkiyat Planlama",
            SistemLog.islem_tipi == "CREATE",
        ).first()
        assert log is not None

    def test_get_sevkiyat_planlari(self, db_session):
        SevkiyatPlaniFactory.create()
        SevkiyatPlaniFactory.create()

        result = get_sevkiyat_planlari(db_session)

        assert len(result) == 2

    def test_get_sevkiyat_planlari_durum_filtre(self, db_session):
        SevkiyatPlaniFactory.create(durum="Planlandi")
        SevkiyatPlaniFactory.create(durum="Yolda")

        result = get_sevkiyat_planlari(db_session, durum="Planlandi")

        assert len(result) == 1

    def test_get_sevkiyat_plani_by_id(self, db_session):
        plan = SevkiyatPlaniFactory.create()

        result = get_sevkiyat_plani(db_session, plan.id)

        assert result is not None
        assert result.id == plan.id

    def test_get_sevkiyat_plani_bulunamadi(self, db_session):
        result = get_sevkiyat_plani(db_session, 99999)
        assert result is None

    def test_update_sevkiyat_plani_basit(self, db_session):
        """Durum değişmeyen basit güncelleme."""
        kullanici = KullaniciFactory.create(rol="admin")
        plan = SevkiyatPlaniFactory.create(durum="Planlandi")

        dto = SevkiyatPlaniUpdate(tir_plaka="06 XYZ 999")
        result = update_sevkiyat_plani(db_session, plan.id, dto, kullanici.id)

        assert result.tir_plaka == "06 XYZ 999"

    def test_update_sevkiyat_yukleniyor_fifo_stok_cikis(self, db_session):
        """Durum Yukleniyor'a geçince FIFO stok çıkışı tetiklenmeli."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()
        lot = LotFactory.create(urun=urun)
        PaletFactory.create(lot=lot, koli_adedi=100)

        siparis = SiparisFactory.create()
        SiparisKalemiFactory.create(siparis=siparis, urun=urun, miktar=20, birim_fiyat=50.0)

        plan = SevkiyatPlaniFactory.create(
            siparis=siparis,
            durum="Planlandi",
            tir_plaka="34 TST 001",
            depo_kapi="Kapi-1",
        )

        dto = SevkiyatPlaniUpdate(durum="Yukleniyor")
        result = update_sevkiyat_plani(db_session, plan.id, dto, kullanici.id)

        assert result.durum == "Yukleniyor"

        # Stok çıkışı oluşturulmuş olmalı
        cikis = db_session.query(StokHareketi).filter(
            StokHareketi.hareket_tipi == "cikis",
            StokHareketi.urun_id == urun.id,
        ).first()
        assert cikis is not None
        assert cikis.miktar == 20

    def test_update_sevkiyat_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = SevkiyatPlaniUpdate(durum="Planlandi")

        result = update_sevkiyat_plani(db_session, 99999, dto, kullanici.id)

        assert result is None

    def test_delete_sevkiyat_plani(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        plan = SevkiyatPlaniFactory.create()

        result = delete_sevkiyat_plani(db_session, plan.id, kullanici.id)

        assert result is True
        assert get_sevkiyat_plani(db_session, plan.id) is None

    def test_delete_sevkiyat_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")

        result = delete_sevkiyat_plani(db_session, 99999, kullanici.id)

        assert result is False
