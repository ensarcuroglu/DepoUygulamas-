"""
API testler: Zonlar endpoint'leri.
"""

import pytest

from tests.factories import ZonFactory

pytestmark = pytest.mark.api


class TestZonEndpoints:
    def test_zon_listele(self, admin_client, db_session):
        ZonFactory.create(isim="Genel Stok", kod="GNL")
        ZonFactory.create(isim="Mal Kabul", kod="MKB")

        response = admin_client.get("/api/zonlar/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_zon_listele_depocu(self, depocu_client, db_session):
        ZonFactory.create(isim="Soguk Depo", kod="SGK")

        response = depocu_client.get("/api/zonlar/")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_zon_olustur(self, admin_client, db_session):
        depo_id = ZonFactory.create().depo_id

        response = admin_client.post(
            "/api/zonlar/",
            json={
                "depo_id": depo_id,
                "isim": "Karantina Alani",
                "tip": "Karantina",
                "kod": "KRN",
                "aciklama": "Izole alan",
                "sira": 5,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["isim"] == "Karantina Alani"
        assert data["tip"] == "Karantina"
        assert data["kod"] == "KRN"

    def test_zon_getir(self, admin_client, db_session):
        zon = ZonFactory.create(isim="Tehlikeli Alan", kod="TEH")

        response = admin_client.get(f"/api/zonlar/{zon.id}")

        assert response.status_code == 200
        assert response.json()["kod"] == "TEH"

    def test_zon_guncelle(self, admin_client, db_session):
        zon = ZonFactory.create(isim="Eski Ad", kod="OLD")

        response = admin_client.put(
            f"/api/zonlar/{zon.id}",
            json={"isim": "Yeni Ad", "sira": 2},
        )

        assert response.status_code == 200
        assert response.json()["isim"] == "Yeni Ad"
        assert response.json()["sira"] == 2

    def test_zon_sil(self, admin_client, db_session):
        zon = ZonFactory.create(kod="DEL")

        response = admin_client.delete(f"/api/zonlar/{zon.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

