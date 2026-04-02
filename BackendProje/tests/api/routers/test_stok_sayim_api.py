"""
API testler: Stok Sayım endpoint'leri.
- GET list/detay/varyans : tüm giriş yapmışlar
- POST baslat           : admin
- POST kalem_kaydet     : tüm giriş yapmışlar
- POST onayla           : admin
"""

import pytest
from tests.factories import StokSayimFactory, UrunFactory

pytestmark = pytest.mark.api


class TestStokSayimEndpoints:
    """Stok sayım endpoint testleri."""

    def test_sayim_listele(self, admin_client, db_session):
        StokSayimFactory.create()
        StokSayimFactory.create()

        response = admin_client.get("/api/stok-sayimlar")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_sayim_listele_depocu(self, depocu_client, db_session):
        """Depocu sayım listesine erişebilmeli."""
        StokSayimFactory.create()

        response = depocu_client.get("/api/stok-sayimlar")

        assert response.status_code == 200

    def test_sayim_baslat(self, admin_client):
        response = admin_client.post("/api/stok-sayimlar", json={
            "aciklama": "Yıllık envanter sayımı",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["durum"] == "devam_ediyor"
        assert data["aciklama"] == "Yıllık envanter sayımı"

    def test_sayim_baslat_depocu_yasak(self, depocu_client):
        """Depocu sayım başlatamamalı — 403."""
        response = depocu_client.post("/api/stok-sayimlar", json={
            "aciklama": "Yetkisiz sayım",
        })

        assert response.status_code == 403

    def test_sayim_getir(self, admin_client, db_session):
        sayim = StokSayimFactory.create(aciklama="Özel sayım")

        response = admin_client.get(f"/api/stok-sayimlar/{sayim.id}")

        assert response.status_code == 200
        assert response.json()["aciklama"] == "Özel sayım"

    def test_sayim_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/stok-sayimlar/99999")
        assert response.status_code == 404

    def test_kalem_kaydet(self, admin_client, db_session):
        sayim = StokSayimFactory.create()
        urun = UrunFactory.create()

        response = admin_client.post(f"/api/stok-sayimlar/{sayim.id}/kalemler", json={
            "urun_id": urun.id,
            "sayilan_miktar": 42,
            "notlar": "Raf A-01 sayıldı",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["urun_id"] == urun.id
        assert data["sayilan_miktar"] == 42

    def test_kalem_kaydet_depocu(self, depocu_client, db_session):
        """Depocu kalem kaydedebilmeli."""
        sayim = StokSayimFactory.create()
        urun = UrunFactory.create()

        response = depocu_client.post(f"/api/stok-sayimlar/{sayim.id}/kalemler", json={
            "urun_id": urun.id,
            "sayilan_miktar": 10,
        })

        assert response.status_code == 200

    def test_varyans_hesapla(self, admin_client, db_session):
        sayim = StokSayimFactory.create()

        response = admin_client.get(f"/api/stok-sayimlar/{sayim.id}/varyans")

        assert response.status_code == 200
        data = response.json()
        assert "sayim_no" in data
        assert "varyanslar" in data

    def test_sayim_onayla(self, admin_client, db_session):
        sayim = StokSayimFactory.create(durum="devam_ediyor")

        response = admin_client.post(f"/api/stok-sayimlar/{sayim.id}/onayla")

        assert response.status_code == 200

    def test_sayim_onayla_depocu_yasak(self, depocu_client, db_session):
        """Depocu sayım onaylayamamalı — 403."""
        sayim = StokSayimFactory.create()

        response = depocu_client.post(f"/api/stok-sayimlar/{sayim.id}/onayla")

        assert response.status_code == 403

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/stok-sayimlar")
        assert response.status_code == 401
