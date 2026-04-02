"""
API testler: Lotlar endpoint'leri — GET: tüm giriş yapmışlar, POST/PUT/DELETE: admin.
"""

import pytest
from datetime import date, timedelta
from tests.factories import LotFactory, UrunFactory

pytestmark = pytest.mark.api


class TestLotEndpoints:
    """Lot CRUD endpoint testleri."""

    def test_lot_listele(self, admin_client, db_session):
        urun = UrunFactory.create()
        LotFactory.create(urun=urun, lot_no="LOT-0001")
        LotFactory.create(urun=urun, lot_no="LOT-0002")

        response = admin_client.get("/api/lotlar/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_lot_listele_depocu(self, depocu_client, db_session):
        """Depocu lot listesine erişebilmeli."""
        UrunFactory.create()

        response = depocu_client.get("/api/lotlar/")

        assert response.status_code == 200

    def test_lot_listele_urun_filtresi(self, admin_client, db_session):
        urun1 = UrunFactory.create()
        urun2 = UrunFactory.create()
        LotFactory.create(urun=urun1)
        LotFactory.create(urun=urun2)

        response = admin_client.get(f"/api/lotlar/?urun_id={urun1.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["urun_id"] == urun1.id

    def test_lot_getir(self, admin_client, db_session):
        lot = LotFactory.create(lot_no="LOT-TEST-001")

        response = admin_client.get(f"/api/lotlar/{lot.id}")

        assert response.status_code == 200
        assert response.json()["lot_no"] == "LOT-TEST-001"

    def test_lot_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/lotlar/99999")
        assert response.status_code == 404

    def test_lot_skt_yaklasan(self, admin_client, db_session):
        urun = UrunFactory.create()
        LotFactory.create(
            urun=urun,
            son_kullanma_tarihi=date.today() + timedelta(days=15),
        )
        LotFactory.create(
            urun=urun,
            son_kullanma_tarihi=date.today() + timedelta(days=365),
        )

        response = admin_client.get("/api/lotlar/skt-yaklasan?gun=30")

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_lot_olustur(self, admin_client, db_session):
        urun = UrunFactory.create()

        response = admin_client.post("/api/lotlar/", json={
            "urun_id": urun.id,
            "lot_no": "LOT-YENI-001",
            "parti_no": "PARTI-2026-001",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["lot_no"] == "LOT-YENI-001"
        assert data["urun_id"] == urun.id

    def test_lot_guncelle(self, admin_client, db_session):
        lot = LotFactory.create()

        response = admin_client.put(f"/api/lotlar/{lot.id}", json={
            "aciklama": "Güncellenmiş lot",
        })

        assert response.status_code == 200
        assert response.json()["aciklama"] == "Güncellenmiş lot"

    def test_lot_sil(self, admin_client, db_session):
        lot = LotFactory.create()

        response = admin_client.delete(f"/api/lotlar/{lot.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/lotlar/")
        assert response.status_code == 401

    def test_depocu_olusturma_yasak(self, depocu_client, db_session):
        """Depocu lot oluşturamamalı — 403."""
        urun = UrunFactory.create()

        response = depocu_client.post("/api/lotlar/", json={
            "urun_id": urun.id,
            "lot_no": "LOT-DEPOCU-001",
        })

        assert response.status_code == 403
