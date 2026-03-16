"""
Integration testler: CRUD fonksiyonları — gerçek MySQL DB ile.
Legacy CRUD katmanının doğru çalıştığını doğrular.
"""

import pytest
from schemas import UrunCreate, UrunUpdate
from crud.urun_crud import (
    get_urunler,
    get_urun,
    get_urun_by_barkod,
    create_urun,
    update_urun,
    delete_urun,
    get_kritik_urunler,
)
from tests.factories import (
    UrunFactory,
    KategoriFactory,
    MarkaFactory,
    KullaniciFactory,
    LotFactory,
    PaletFactory,
)

pytestmark = pytest.mark.integration


class TestUrunCrud:
    """Urun CRUD fonksiyonları integration testleri."""

    def test_create_urun(self, db_session):
        """Yeni ürün oluşturma ve DB'ye kaydetme."""
        kategori = KategoriFactory.create()
        marka = MarkaFactory.create()
        kullanici = KullaniciFactory.create(rol="admin")

        dto = UrunCreate(
            isim="Integration Test Ürün",
            barkod="1111111111111",
            kategori_id=kategori.id,
            marka_id=marka.id,
            birim="Adet",
            fiyat=99.90,
            min_stok=5,
        )

        urun = create_urun(db_session, dto, kullanici.id)

        assert urun.id is not None
        assert urun.isim == "Integration Test Ürün"
        assert urun.kategori_id == kategori.id
        assert urun.marka_id == marka.id

    def test_get_urun_by_id(self, db_session):
        """ID ile ürün getirme."""
        urun = UrunFactory.create()

        result = get_urun(db_session, urun.id)

        assert result is not None
        assert result.id == urun.id
        assert result.isim == urun.isim

    def test_get_urun_by_id_bulunamadi(self, db_session):
        """Olmayan ID için None dönmeli."""
        result = get_urun(db_session, 99999)
        assert result is None

    def test_get_urun_by_barkod(self, db_session):
        """Barkod ile ürün getirme."""
        urun = UrunFactory.create(barkod="2222222222222")

        result = get_urun_by_barkod(db_session, "2222222222222")

        assert result is not None
        assert result.barkod == "2222222222222"

    def test_get_urunler_search(self, db_session):
        """İsim aramasıyla ürün listeleme."""
        UrunFactory.create(isim="Elma Suyu")
        UrunFactory.create(isim="Portakal Suyu")
        UrunFactory.create(isim="Çikolata")

        result = get_urunler(db_session, search="Suyu")

        assert len(result) == 2

    def test_get_urunler_kategori_filtre(self, db_session):
        """Kategori filtreleme."""
        kat1 = KategoriFactory.create(isim="Gıda")
        kat2 = KategoriFactory.create(isim="Temizlik")
        UrunFactory.create(kategori=kat1)
        UrunFactory.create(kategori=kat1)
        UrunFactory.create(kategori=kat2)

        result = get_urunler(db_session, kategori_id=kat1.id)

        assert len(result) == 2

    def test_update_urun(self, db_session):
        """Ürün güncelleme."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create(isim="Eski İsim", fiyat=10.0)

        dto = UrunUpdate(isim="Yeni İsim", fiyat=20.0)
        updated = update_urun(db_session, urun.id, dto, kullanici.id)

        assert updated.isim == "Yeni İsim"
        assert updated.fiyat == 20.0

    def test_delete_urun_soft_delete(self, db_session):
        """Silme işlemi aktif=False yapmalı (soft delete)."""
        kullanici = KullaniciFactory.create(rol="admin")
        urun = UrunFactory.create()

        result = delete_urun(db_session, urun.id, kullanici.id)

        assert result is True

        # Soft delete kontrolü
        deleted = get_urun(db_session, urun.id)
        assert deleted is not None
        assert deleted.aktif is False

    def test_get_kritik_urunler(self, db_session):
        """Stok miktarı min_stok'un altında olan ürünler."""
        # min_stok=10 olan ürün, stok=0 (palet yok)
        urun_kritik = UrunFactory.create(min_stok=10)

        # min_stok=5 olan ürün, stok > min_stok (palet ile)
        urun_normal = UrunFactory.create(min_stok=5)
        lot = LotFactory.create(urun=urun_normal)
        PaletFactory.create(lot=lot, koli_adedi=100)

        # Session'ı yenileyerek column_property'nin hesaplanmasını sağla
        db_session.expire_all()

        result = get_kritik_urunler(db_session)
        kritik_ids = [u.id for u in result]

        assert urun_kritik.id in kritik_ids
        assert urun_normal.id not in kritik_ids
