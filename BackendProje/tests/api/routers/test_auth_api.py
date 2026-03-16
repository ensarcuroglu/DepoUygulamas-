"""
API testler: Auth endpoint'leri — tam HTTP döngüsü.
Login, register, me, logout endpoint'lerini test eder.
"""

import pytest
from tests.factories import KullaniciFactory
from tests.conftest import TEST_PASSWORD

pytestmark = pytest.mark.api


class TestLoginEndpoint:
    """POST /api/auth/login testleri."""

    def test_basarili_login(self, client, db_session):
        """Doğru credentials ile login başarılı olmalı."""
        KullaniciFactory.create(
            kullanici_adi="logintest",
            rol="admin",
        )

        response = client.post("/api/auth/login", json={
            "kullanici_adi": "logintest",
            "sifre": TEST_PASSWORD,
        })

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["kullanici_adi"] == "logintest"
        assert data["user"]["rol"] == "admin"

    def test_yanlis_sifre(self, client, db_session):
        """Yanlış şifre ile 401 dönmeli."""
        KullaniciFactory.create(kullanici_adi="wrongpass")

        response = client.post("/api/auth/login", json={
            "kullanici_adi": "wrongpass",
            "sifre": "YanlisParola1",
        })

        assert response.status_code == 401

    def test_olmayan_kullanici(self, client):
        """Olmayan kullanıcı ile 401 dönmeli."""
        response = client.post("/api/auth/login", json={
            "kullanici_adi": "yok_kullanici",
            "sifre": TEST_PASSWORD,
        })

        assert response.status_code == 401


class TestMeEndpoint:
    """GET /api/auth/me testleri."""

    def test_yetkili_erisim(self, admin_client):
        """Geçerli token ile kullanıcı bilgisi dönmeli."""
        response = admin_client.get("/api/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["kullanici_adi"] == "test_admin"
        assert data["rol"] == "admin"

    def test_yetkisiz_erisim(self, client):
        """Token olmadan 401 dönmeli."""
        response = client.get("/api/auth/me")

        assert response.status_code == 401


class TestRegisterEndpoint:
    """POST /api/auth/register testleri."""

    def test_admin_kayit_olustur(self, admin_client):
        """Admin yeni kullanıcı oluşturabilmeli."""
        response = admin_client.post("/api/auth/register", json={
            "kullanici_adi": "yeni_depocu",
            "ad_soyad": "Yeni Depocu",
            "sifre": TEST_PASSWORD,
            "rol": "depocu",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["kullanici_adi"] == "yeni_depocu"
        assert data["rol"] == "depocu"

    def test_depocu_kayit_olusturamaz(self, depocu_client):
        """Depocu kullanıcı oluşturamamalı — 403."""
        response = depocu_client.post("/api/auth/register", json={
            "kullanici_adi": "deneme",
            "ad_soyad": "Deneme User",
            "sifre": TEST_PASSWORD,
        })

        assert response.status_code == 403

    def test_tekrar_eden_kullanici_adi(self, admin_client, db_session):
        """Aynı kullanıcı adı ile kayıt 400 dönmeli."""
        KullaniciFactory.create(kullanici_adi="mevcut_user")

        response = admin_client.post("/api/auth/register", json={
            "kullanici_adi": "mevcut_user",
            "ad_soyad": "Tekrar",
            "sifre": TEST_PASSWORD,
        })

        assert response.status_code == 400
