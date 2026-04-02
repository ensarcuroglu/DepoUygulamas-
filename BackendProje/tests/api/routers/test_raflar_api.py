"""
API testler: Raflar endpoint'leri — GET: admin/lojistik/depocu, POST/PUT/DELETE: admin/lojistik.
"""

import pytest
from tests.factories import DepoFactory, RafFactory

pytestmark = pytest.mark.api


class TestRafEndpoints:
    """Raf CRUD endpoint testleri."""

    def test_raf_listele(self, admin_client, db_session):
        depo = DepoFactory.create()
        RafFactory.create(depo=depo, kod="A-01")
        RafFactory.create(depo=depo, kod="A-02")

        response = admin_client.get("/api/raflar/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_raf_listele_depocu(self, depocu_client, db_session):
        """Depocu raf listesine erişebilmeli."""
        DepoFactory.create()

        response = depocu_client.get("/api/raflar/")

        assert response.status_code == 200

    def test_raf_listele_depo_filtresi(self, admin_client, db_session):
        depo1 = DepoFactory.create()
        depo2 = DepoFactory.create()
        RafFactory.create(depo=depo1)
        RafFactory.create(depo=depo2)

        response = admin_client.get(f"/api/raflar/?depo_id={depo1.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["depo_id"] == depo1.id

    def test_raf_olustur(self, admin_client, db_session):
        depo = DepoFactory.create()

        response = admin_client.post("/api/raflar/", json={
            "depo_id": depo.id,
            "kod": "B-01",
            "bolge": "Üst Kat",
            "kapasite": 50,
        })

        assert response.status_code == 201
        data = response.json()
        assert data["kod"] == "B-01"
        assert data["depo_id"] == depo.id

    def test_raf_getir(self, admin_client, db_session):
        raf = RafFactory.create(kod="C-03")

        response = admin_client.get(f"/api/raflar/{raf.id}")

        assert response.status_code == 200
        assert response.json()["kod"] == "C-03"

    def test_raf_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/raflar/99999")
        assert response.status_code == 404

    def test_raf_guncelle(self, admin_client, db_session):
        raf = RafFactory.create(kapasite=100)

        response = admin_client.put(f"/api/raflar/{raf.id}", json={
            "kapasite": 200,
        })

        assert response.status_code == 200
        assert response.json()["kapasite"] == 200

    def test_raf_sil(self, admin_client, db_session):
        raf = RafFactory.create()

        response = admin_client.delete(f"/api/raflar/{raf.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/raflar/")
        assert response.status_code == 401

    def test_depocu_olusturma_yasak(self, depocu_client, db_session):
        """Depocu raf oluşturamamalı — 403."""
        depo = DepoFactory.create()

        response = depocu_client.post("/api/raflar/", json={
            "depo_id": depo.id,
            "kod": "Z-99",
        })

        assert response.status_code == 403
