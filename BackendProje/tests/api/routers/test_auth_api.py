"""
API testler: Auth endpoint'leri — tam HTTP döngüsü.
Login, register, me, logout endpoint'lerini test eder.
"""

import pytest
from datetime import datetime, timedelta
from app.core.auth import hash_token # Gerekli yardımcıları içe aktar
from tests.factories import KullaniciFactory, DepoFactory
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

    def test_admin_gecerli_depo_atamasi_ile_kayit_olusturur(self, admin_client):
        """Geçerli depo_id ile kullanıcı oluşturma başarılı olmalı."""
        depo = DepoFactory.create(isim="Ana Depo")

        response = admin_client.post("/api/auth/register", json={
            "kullanici_adi": "depolu_user",
            "ad_soyad": "Depolu Kullanıcı",
            "sifre": TEST_PASSWORD,
            "rol": "depocu",
            "depo_id": depo.id,
        })

        assert response.status_code == 201
        data = response.json()
        assert data["kullanici_adi"] == "depolu_user"
        assert data["depo_id"] == depo.id
        assert data["depo_erisimi_yok"] is False

    def test_admin_hicbir_depoda_yetkisi_olmayan_kullanici_olusturur(self, admin_client):
        """Yeni kullanıcı hiçbir depoda yetkili olmayacak şekilde oluşturulabilmeli."""
        response = admin_client.post("/api/auth/register", json={
            "kullanici_adi": "yetkisiz_user",
            "ad_soyad": "Yetkisiz Kullanıcı",
            "sifre": TEST_PASSWORD,
            "rol": "depocu",
            "depo_erisimi_yok": True,
        })

        assert response.status_code == 201
        data = response.json()
        assert data["kullanici_adi"] == "yetkisiz_user"
        assert data["depo_id"] is None
        assert data["depo_erisimi_yok"] is True

    def test_admin_gecersiz_depo_ile_kayit_olusturamaz(self, admin_client):
        """Olmayan depo_id ile kayıt 404 dönmeli."""
        response = admin_client.post("/api/auth/register", json={
            "kullanici_adi": "hatali_depo_user",
            "ad_soyad": "Hatalı Depo",
            "sifre": TEST_PASSWORD,
            "rol": "depocu",
            "depo_id": 99999,
        })

        assert response.status_code == 404

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


class TestRefreshEndpoint:
    """POST /api/auth/refresh testleri."""

    def test_basarili_refresh(self, client, db_session):
        """Geçerli bir refresh token ile yeni access token alınabilmeli."""
        user = KullaniciFactory.create(kullanici_adi="refreshtest")
        # Manuel refresh token oluştur ve DB'ye hash'le
        raw_token = "id_dogru_token_dogru"
        user.refresh_token_hash = hash_token(raw_token)
        user.refresh_token_son_kullanim = datetime.utcnow() + timedelta(days=1)
        db_session.commit()

        # O(1) formatı: {id}:{raw_token}
        refresh_input = f"{user.id}:{raw_token}"

        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_input})

        assert response.status_code == 200
        assert "access_token" in response.json()
        assert response.json()["token_type"] == "bearer"

    def test_yanlis_id_ile_refresh_hatasi(self, client):
        """Token içindeki ID veritabanında yoksa 401 dönmeli (O(1) Fail)."""
        # Veritabanında olmayan bir ID: 99999
        refresh_input = "99999:rastgele_token"

        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_input})

        assert response.status_code == 401
        assert "Geçersiz" in response.json()["detail"]

    def test_hatali_format_refresh_hatasi(self, client):
        """İki nokta (:) içermeyen hatalı format 401 dönmeli."""
        response = client.post("/api/auth/refresh", json={"refresh_token": "sadece_string_format_yanlis"})

        assert response.status_code == 401

    def test_suresi_dolmus_refresh_hatasi(self, client, db_session):
        """Süresi dolmuş refresh token reddedilmeli."""
        user = KullaniciFactory.create()
        user.refresh_token_hash = hash_token("token")
        user.refresh_token_son_kullanim = datetime.utcnow() - timedelta(minutes=1) # Süresi dolmuş
        db_session.commit()

        refresh_input = f"{user.id}:token"
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_input})

        assert response.status_code == 401


class TestLogoutEndpoint:
    """POST /api/auth/logout testleri."""

    def test_logout_basarili_olmali(self, admin_client, db_session):
        """Logout sonrası kullanıcının refresh token hash'i temizlenmeli."""
        # admin_client fixture'ı zaten bir kullanıcı oluşturur
        from models import Kullanici
        user = db_session.query(Kullanici).filter(Kullanici.kullanici_adi == "test_admin").first()
        
        # Önce bir hash var mı kontrol et (login olmuş sayıyoruz)
        user.refresh_token_hash = "mevcut_hash"
        db_session.commit()

        response = admin_client.post("/api/auth/logout")

        assert response.status_code == 200
        
        # DB'yi tazele ve hash'in silindiğini doğrula
        db_session.refresh(user)
        assert user.refresh_token_hash is None

    def test_logout_sonrasi_refresh_yapilamamali(self, client, db_session):
        """Logout olmuş (hash'i silinmiş) bir token ile refresh yapılamamalı."""
        user = KullaniciFactory.create()
        user.refresh_token_hash = None # Logout olmuş veya hiç login olmamış
        db_session.commit()

        refresh_input = f"{user.id}:token"
        response = client.post("/api/auth/refresh", json={"refresh_token": refresh_input})

        assert response.status_code == 401
