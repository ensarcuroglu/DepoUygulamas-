"""
API testler: Depolar endpoint'leri — admin + lojistik erişimi.
"""

import pytest
from tests.factories import DepoFactory

pytestmark = pytest.mark.api


class TestDepoEndpoints:
    """Depo CRUD endpoint testleri."""

    def test_depo_listele(self, admin_client, db_session):
        DepoFactory.create(isim="Depo A")
        DepoFactory.create(isim="Depo B")

        response = admin_client.get("/api/depolar/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_depo_listele_lojistik(self, lojistik_client, db_session):
        DepoFactory.create(isim="Merkez Depo")

        response = lojistik_client.get("/api/depolar/")

        assert response.status_code == 200

    def test_depo_olustur(self, admin_client):
        response = admin_client.post("/api/depolar/", json={
            "isim": "Yeni Depo",
            "adres": "Istanbul, Turkiye",
            "aciklama": "Test deposu",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["isim"] == "Yeni Depo"
        assert data["aktif"] is True

    def test_depo_olustur_lojistik(self, lojistik_client):
        response = lojistik_client.post("/api/depolar/", json={
            "isim": "Lojistik Deposu",
        })

        assert response.status_code == 201

    def test_depo_getir(self, admin_client, db_session):
        depo = DepoFactory.create(isim="Batı Depo")

        response = admin_client.get(f"/api/depolar/{depo.id}")

        assert response.status_code == 200
        assert response.json()["isim"] == "Batı Depo"

    def test_depo_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/depolar/99999")
        assert response.status_code == 404

    def test_depo_guncelle(self, admin_client, db_session):
        depo = DepoFactory.create(isim="Eski Depo")

        response = admin_client.put(f"/api/depolar/{depo.id}", json={
            "isim": "Yenilenmiş Depo",
        })

        assert response.status_code == 200
        assert response.json()["isim"] == "Yenilenmiş Depo"

    def test_depo_sil(self, admin_client, db_session):
        depo = DepoFactory.create()

        response = admin_client.delete(f"/api/depolar/{depo.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/depolar/")
        assert response.status_code == 401

    def test_depocu_erisim_yasak(self, depocu_client):
        """Depocu depo listeleyememeli — 403."""
        response = depocu_client.get("/api/depolar/")
        assert response.status_code == 403
