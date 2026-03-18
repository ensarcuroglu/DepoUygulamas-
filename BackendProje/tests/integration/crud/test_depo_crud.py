"""Integration testler: Depo CRUD — gerçek MySQL DB ile."""

import pytest
from crud.depo_crud import (
    get_depolar,
    get_depo,
    create_depo,
    update_depo,
    delete_depo,
)
from schemas import DepoCreate, DepoUpdate
from models import SistemLog
from tests.factories import DepoFactory, KullaniciFactory

pytestmark = pytest.mark.integration


class TestDepoCrud:

    def test_create_depo(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = DepoCreate(isim="Ana Depo", adres="Istanbul", aciklama="Merkez depo")

        result = create_depo(db_session, dto, kullanici.id)

        assert result.id is not None
        assert result.isim == "Ana Depo"
        assert result.adres == "Istanbul"
        assert result.aktif is True

    def test_create_depo_sistem_log(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = DepoCreate(isim="Log Test Depo")

        create_depo(db_session, dto, kullanici.id)

        log = db_session.query(SistemLog).filter(
            SistemLog.modul == "Depo Yönetimi",
            SistemLog.islem_tipi == "CREATE",
        ).first()
        assert log is not None
        assert "Log Test Depo" in log.detay

    def test_get_depolar(self, db_session):
        DepoFactory.create(isim="Depo A")
        DepoFactory.create(isim="Depo B")
        DepoFactory.create(isim="Pasif Depo", aktif=False)

        result = get_depolar(db_session)

        assert len(result) == 2

    def test_get_depolar_dahil_pasif(self, db_session):
        DepoFactory.create(isim="Aktif")
        DepoFactory.create(isim="Pasif", aktif=False)

        result = get_depolar(db_session, sadece_aktif=False)

        assert len(result) == 2

    def test_get_depo_by_id(self, db_session):
        depo = DepoFactory.create(isim="Depo X")

        result = get_depo(db_session, depo.id)

        assert result is not None
        assert result.isim == "Depo X"

    def test_get_depo_bulunamadi(self, db_session):
        result = get_depo(db_session, 99999)
        assert result is None

    def test_update_depo(self, db_session):
        depo = DepoFactory.create(isim="Eski")

        dto = DepoUpdate(isim="Yeni", adres="Ankara")
        result = update_depo(db_session, depo.id, dto)

        assert result.isim == "Yeni"
        assert result.adres == "Ankara"

    def test_update_depo_bulunamadi(self, db_session):
        dto = DepoUpdate(isim="X")

        result = update_depo(db_session, 99999, dto)

        assert result is None

    def test_delete_depo_soft(self, db_session):
        depo = DepoFactory.create(isim="Silinecek")

        result = delete_depo(db_session, depo.id)

        assert result is True
        deleted = get_depo(db_session, depo.id)
        assert deleted.aktif is False

    def test_delete_depo_bulunamadi(self, db_session):
        result = delete_depo(db_session, 99999)
        assert result is False
