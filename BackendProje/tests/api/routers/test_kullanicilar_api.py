"""
API testler: Kullanıcı Yönetimi endpoint'leri.
- GET /api/kullanicilar/     : admin
- GET /api/kullanicilar/{id} : admin
- PUT /api/kullanicilar/{id} : get_current_user (use case erişim kontrolü yapar)
- DELETE /api/kullanicilar/{id}: admin
"""

import pytest
from tests.factories import KullaniciFactory

pytestmark = pytest.mark.api


class TestKullaniciEndpoints:
    """Kullanıcı yönetimi endpoint testleri."""

    def test_kullanici_listele(self, admin_client, db_session):
        KullaniciFactory.create(kullanici_adi="user_a")
        KullaniciFactory.create(kullanici_adi="user_b")

        response = admin_client.get("/api/kullanicilar/")

        assert response.status_code == 200
        # admin_user fixture de listeye girer; en az 3 kullanıcı
        assert len(response.json()) >= 2

    def test_kullanici_listele_depocu_yasak(self, depocu_client):
        """Depocu kullanıcıları listeleyememeli — 403."""
        response = depocu_client.get("/api/kullanicilar/")
        assert response.status_code == 403

    def test_kullanici_getir(self, admin_client, db_session):
        kullanici = KullaniciFactory.create(kullanici_adi="getir_test")

        response = admin_client.get(f"/api/kullanicilar/{kullanici.id}")

        assert response.status_code == 200
        assert response.json()["kullanici_adi"] == "getir_test"

    def test_kullanici_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/kullanicilar/99999")
        assert response.status_code == 404

    def test_kullanici_guncelle_admin(self, admin_client, db_session):
        kullanici = KullaniciFactory.create(ad_soyad="Eski Ad")

        response = admin_client.put(f"/api/kullanicilar/{kullanici.id}", json={
            "ad_soyad": "Yeni Ad",
        })

        assert response.status_code == 200
        assert response.json()["ad_soyad"] == "Yeni Ad"

    def test_kullanici_guncelle_kendi_profili(self, depocu_client, depocu_user):
        """Depocu kendi profilini güncelleyebilmeli."""
        kullanici, _ = depocu_user

        response = depocu_client.put(f"/api/kullanicilar/{kullanici.id}", json={
            "ad_soyad": "Depocu Yeni Ad",
        })

        assert response.status_code == 200
        assert response.json()["ad_soyad"] == "Depocu Yeni Ad"

    def test_kullanici_sil(self, admin_client, db_session):
        kullanici = KullaniciFactory.create(kullanici_adi="silinecek_user")

        response = admin_client.delete(f"/api/kullanicilar/{kullanici.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_kullanici_sil_depocu_yasak(self, depocu_client, db_session):
        """Depocu başka kullanıcı silemez — 403."""
        hedef = KullaniciFactory.create(kullanici_adi="hedef_user")

        response = depocu_client.delete(f"/api/kullanicilar/{hedef.id}")

        assert response.status_code == 403

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/kullanicilar/")
        assert response.status_code == 401
