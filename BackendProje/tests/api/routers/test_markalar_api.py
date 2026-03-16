"""
API testler: Markalar endpoint'leri — rol kontrolleri.
"""

import pytest
from tests.factories import MarkaFactory

pytestmark = pytest.mark.api


class TestMarkaEndpoints:
    """Marka CRUD endpoint testleri."""

    def test_marka_listele(self, admin_client, db_session):
        MarkaFactory.create(isim="Marka A")
        MarkaFactory.create(isim="Marka B")

        response = admin_client.get("/api/markalar/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_marka_olustur(self, admin_client):
        response = admin_client.post("/api/markalar/", json={
            "isim": "Yeni Marka",
            "aciklama": "Test açıklama",
        })

        assert response.status_code == 200
        assert response.json()["isim"] == "Yeni Marka"

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/markalar/")
        assert response.status_code == 401

    def test_depocu_erisim(self, depocu_client):
        """Depocu marka oluşturamamalı — 403."""
        response = depocu_client.post("/api/markalar/", json={
            "isim": "Depocu Marka",
        })

        assert response.status_code == 403
