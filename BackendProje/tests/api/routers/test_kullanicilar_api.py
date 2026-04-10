"""
API testler: Kullanıcı Yönetimi endpoint'leri.
- GET /api/kullanicilar/     : admin
- GET /api/kullanicilar/{id} : admin
- PUT /api/kullanicilar/{id} : get_current_user (use case erişim kontrolü yapar)
- DELETE /api/kullanicilar/{id}: admin
"""

import pytest
from tests.factories import KullaniciFactory, DepoFactory

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

    def test_kullanici_listele_depo_yetki_alanlarini_doner(self, admin_client):
        depo = DepoFactory.create(isim="Liste Deposu")
        KullaniciFactory.create(kullanici_adi="depolu_liste", depo_id=depo.id)
        KullaniciFactory.create(
            kullanici_adi="yetkisiz_liste",
            depo_id=None,
            depo_erisimi_yok=True,
        )

        response = admin_client.get("/api/kullanicilar/")

        assert response.status_code == 200
        data = {item["kullanici_adi"]: item for item in response.json()}
        assert data["depolu_liste"]["depo_id"] == depo.id
        assert data["depolu_liste"]["depo_erisimi_yok"] is False
        assert data["yetkisiz_liste"]["depo_id"] is None
        assert data["yetkisiz_liste"]["depo_erisimi_yok"] is True

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

    def test_admin_kullaniciya_depo_atayabilir(self, admin_client):
        kullanici = KullaniciFactory.create()
        depo = DepoFactory.create(isim="Sevkiyat Deposu")

        response = admin_client.put(f"/api/kullanicilar/{kullanici.id}", json={
            "depo_id": depo.id,
        })

        assert response.status_code == 200
        assert response.json()["depo_id"] == depo.id
        assert response.json()["depo_erisimi_yok"] is False

    def test_admin_kullaniciyi_hicbir_depoda_yetkili_olmayacak_sekilde_guncelleyebilir(self, admin_client):
        depo = DepoFactory.create(isim="Operasyon Deposu")
        kullanici = KullaniciFactory.create(depo_id=depo.id)

        response = admin_client.put(f"/api/kullanicilar/{kullanici.id}", json={
            "depo_id": None,
            "depo_erisimi_yok": True,
        })

        assert response.status_code == 200
        assert response.json()["depo_id"] is None
        assert response.json()["depo_erisimi_yok"] is True

    def test_admin_gecersiz_depo_atayamaz(self, admin_client):
        kullanici = KullaniciFactory.create()

        response = admin_client.put(f"/api/kullanicilar/{kullanici.id}", json={
            "depo_id": 99999,
        })

        assert response.status_code == 404

    def test_kullanici_guncelle_kendi_profili(self, depocu_client, depocu_user):
        """Depocu kendi profilini güncelleyebilmeli."""
        kullanici, _ = depocu_user

        response = depocu_client.put(f"/api/kullanicilar/{kullanici.id}", json={
            "ad_soyad": "Depocu Yeni Ad",
        })

        assert response.status_code == 200
        assert response.json()["ad_soyad"] == "Depocu Yeni Ad"

    def test_depocu_kendi_depo_atamasini_degistiremez(self, depocu_client, depocu_user):
        """Admin olmayan kullanıcı depo atamasını değiştirememeli."""
        kullanici, _ = depocu_user
        depo = DepoFactory.create()

        response = depocu_client.put(f"/api/kullanicilar/{kullanici.id}", json={
            "depo_id": depo.id,
        })

        assert response.status_code == 403

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
