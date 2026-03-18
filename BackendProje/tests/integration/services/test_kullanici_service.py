"""Integration testler: KullaniciService — gerçek MySQL DB ile."""

import pytest
from services.kullanici_service import KullaniciService
from schemas import KullaniciUpdate
from core.exceptions import NotFoundError, DuplicateError, PermissionDeniedError, BadRequestError
from tests.factories import KullaniciFactory

pytestmark = pytest.mark.integration


class TestKullaniciService:

    def test_get_kullanicilar(self, db_session):
        KullaniciFactory.create()
        KullaniciFactory.create()

        result = KullaniciService.get_kullanicilar(db_session)

        assert len(result) == 2

    def test_get_kullanici(self, db_session):
        user = KullaniciFactory.create(ad_soyad="Ali Veli")

        result = KullaniciService.get_kullanici(db_session, user.id)

        assert result.ad_soyad == "Ali Veli"

    def test_get_kullanici_bulunamadi(self, db_session):
        with pytest.raises(NotFoundError):
            KullaniciService.get_kullanici(db_session, 99999)

    def test_update_kullanici_kendi_hesabi(self, db_session):
        """Kullanıcı kendi ad_soyad'ını güncelleyebilmeli."""
        user = KullaniciFactory.create(ad_soyad="Eski Ad")

        dto = KullaniciUpdate(ad_soyad="Yeni Ad")
        result = KullaniciService.update_kullanici(db_session, user.id, dto, user)

        assert result.ad_soyad == "Yeni Ad"

    def test_update_kullanici_admin_baskasini_guncelleyebilir(self, db_session):
        admin = KullaniciFactory.create(rol="admin")
        user = KullaniciFactory.create(ad_soyad="Eski")

        dto = KullaniciUpdate(ad_soyad="Admin Guncelledi")
        result = KullaniciService.update_kullanici(db_session, user.id, dto, admin)

        assert result.ad_soyad == "Admin Guncelledi"

    def test_update_kullanici_yetkisiz(self, db_session):
        """Admin olmayan kullanıcı başkasını güncelleyemez."""
        user1 = KullaniciFactory.create(rol="depocu")
        user2 = KullaniciFactory.create(rol="depocu")

        dto = KullaniciUpdate(ad_soyad="Hack")

        with pytest.raises(PermissionDeniedError):
            KullaniciService.update_kullanici(db_session, user2.id, dto, user1)

    def test_update_kullanici_duplicate_username(self, db_session):
        """Var olan kullanıcı adı ile güncelleme hata vermeli."""
        admin = KullaniciFactory.create(rol="admin", kullanici_adi="admin1")
        user = KullaniciFactory.create(kullanici_adi="user1")

        dto = KullaniciUpdate(kullanici_adi="admin1")

        with pytest.raises(DuplicateError):
            KullaniciService.update_kullanici(db_session, user.id, dto, admin)

    def test_update_kullanici_rol_degistirme_admin(self, db_session):
        """Admin rol değiştirebilmeli."""
        admin = KullaniciFactory.create(rol="admin")
        user = KullaniciFactory.create(rol="depocu")

        dto = KullaniciUpdate(rol="lojistik")
        result = KullaniciService.update_kullanici(db_session, user.id, dto, admin)

        assert result.rol == "lojistik"

    def test_update_kullanici_rol_degistirme_yetkisiz(self, db_session):
        """Depocu kendi rolünü değiştiremez."""
        user = KullaniciFactory.create(rol="depocu")

        dto = KullaniciUpdate(rol="admin")

        with pytest.raises(PermissionDeniedError):
            KullaniciService.update_kullanici(db_session, user.id, dto, user)

    def test_update_kullanici_sifre(self, db_session):
        """Şifre güncellemesi hash'lenmiş olmalı."""
        user = KullaniciFactory.create()
        eski_hash = user.sifre_hash

        dto = KullaniciUpdate(sifre="YeniSifre123!")
        result = KullaniciService.update_kullanici(db_session, user.id, dto, user)

        assert result.sifre_hash != eski_hash

    def test_delete_kullanici(self, db_session):
        admin = KullaniciFactory.create(rol="admin")
        user = KullaniciFactory.create()

        result = KullaniciService.delete_kullanici(db_session, user.id, admin)

        assert result["message"] == "Kullanıcı başarıyla silindi"
        assert result["id"] == user.id

    def test_delete_kullanici_kendini_silemez(self, db_session):
        admin = KullaniciFactory.create(rol="admin")

        with pytest.raises(BadRequestError):
            KullaniciService.delete_kullanici(db_session, admin.id, admin)

    def test_delete_kullanici_bulunamadi(self, db_session):
        admin = KullaniciFactory.create(rol="admin")

        with pytest.raises(NotFoundError):
            KullaniciService.delete_kullanici(db_session, 99999, admin)
