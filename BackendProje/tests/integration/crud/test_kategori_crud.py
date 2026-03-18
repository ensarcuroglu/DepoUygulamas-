"""Integration testler: Kategori CRUD — gerçek MySQL DB ile."""

import pytest
from crud.kategori_crud import (
    get_kategoriler,
    get_kategori,
    create_kategori,
    update_kategori,
    delete_kategori,
)
from schemas import KategoriCreate, KategoriUpdate
from models import SistemLog
from tests.factories import KategoriFactory, KullaniciFactory

pytestmark = pytest.mark.integration


class TestKategoriCrud:

    def test_create_kategori(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = KategoriCreate(isim="Elektronik", aciklama="Elektronik urunler")

        result = create_kategori(db_session, dto, kullanici.id)

        assert result.id is not None
        assert result.isim == "Elektronik"
        assert result.aciklama == "Elektronik urunler"
        assert result.aktif is True

    def test_create_kategori_sistem_log(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = KategoriCreate(isim="Gida")

        create_kategori(db_session, dto, kullanici.id)

        log = db_session.query(SistemLog).filter(
            SistemLog.modul == "Kategori Yönetimi",
            SistemLog.islem_tipi == "CREATE",
        ).first()
        assert log is not None
        assert "Gida" in log.detay

    def test_get_kategoriler(self, db_session):
        KategoriFactory.create(isim="Gida")
        KategoriFactory.create(isim="Temizlik")
        KategoriFactory.create(isim="Pasif", aktif=False)

        result = get_kategoriler(db_session)

        assert len(result) == 2

    def test_get_kategoriler_dahil_pasif(self, db_session):
        KategoriFactory.create(isim="Aktif")
        KategoriFactory.create(isim="Pasif", aktif=False)

        result = get_kategoriler(db_session, sadece_aktif=False)

        assert len(result) == 2

    def test_get_kategori_by_id(self, db_session):
        kat = KategoriFactory.create(isim="Test Kategori")

        result = get_kategori(db_session, kat.id)

        assert result is not None
        assert result.isim == "Test Kategori"

    def test_get_kategori_bulunamadi(self, db_session):
        result = get_kategori(db_session, 99999)
        assert result is None

    def test_update_kategori(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        kat = KategoriFactory.create(isim="Eski Isim")

        dto = KategoriUpdate(isim="Yeni Isim")
        result = update_kategori(db_session, kat.id, dto, kullanici.id)

        assert result.isim == "Yeni Isim"

    def test_update_kategori_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        dto = KategoriUpdate(isim="X")

        result = update_kategori(db_session, 99999, dto, kullanici.id)

        assert result is None

    def test_delete_kategori_soft(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")
        kat = KategoriFactory.create(isim="Silinecek")

        result = delete_kategori(db_session, kat.id, kullanici.id)

        assert result is True
        deleted = get_kategori(db_session, kat.id)
        assert deleted.aktif is False

    def test_delete_kategori_bulunamadi(self, db_session):
        kullanici = KullaniciFactory.create(rol="admin")

        result = delete_kategori(db_session, 99999, kullanici.id)

        assert result is False
