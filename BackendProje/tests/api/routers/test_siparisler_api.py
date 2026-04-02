"""
API testler: Siparişler endpoint'leri — admin + lojistik erişimi.
"""

import pytest
from datetime import date, timedelta
from tests.factories import SiparisFactory, UrunFactory

pytestmark = pytest.mark.api


def _gelecek_tarih(gun: int = 7) -> str:
    return (date.today() + timedelta(days=gun)).isoformat()


class TestSiparisEndpoints:
    """Sipariş CRUD endpoint testleri."""

    def test_siparis_listele(self, admin_client, db_session):
        SiparisFactory.create(musteri_adi="Müşteri A")
        SiparisFactory.create(musteri_adi="Müşteri B")

        response = admin_client.get("/api/siparisler/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_siparis_listele_lojistik(self, lojistik_client, db_session):
        SiparisFactory.create()

        response = lojistik_client.get("/api/siparisler/")

        assert response.status_code == 200

    def test_siparis_listele_durum_filtresi(self, admin_client, db_session):
        SiparisFactory.create(durum="Bekleme")
        SiparisFactory.create(durum="Hazirlaniyor")

        response = admin_client.get("/api/siparisler/?durum=Bekleme")

        assert response.status_code == 200
        data = response.json()
        assert all(s["durum"] == "Bekleme" for s in data)

    def test_siparis_olustur(self, admin_client, db_session):
        urun = UrunFactory.create()

        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": "Test Müşteri",
            "teslimat_adresi": "Test Adres, İstanbul",
            "teslimat_tarihi": _gelecek_tarih(),
            "notlar": "",
            "kalemler": [
                {
                    "urun_id": urun.id,
                    "miktar": 5,
                    "birim_fiyat": 100.0,
                    "kdv_orani": 18.0,
                }
            ],
        })

        assert response.status_code == 201
        data = response.json()
        assert data["musteri_adi"] == "Test Müşteri"
        assert data["durum"] == "Bekleme"
        assert len(data["kalemler"]) == 1

    def test_siparis_getir(self, admin_client, db_session):
        siparis = SiparisFactory.create(musteri_adi="Detay Müşteri")

        response = admin_client.get(f"/api/siparisler/{siparis.id}")

        assert response.status_code == 200
        assert response.json()["musteri_adi"] == "Detay Müşteri"

    def test_siparis_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/siparisler/99999")
        assert response.status_code == 404

    def test_siparis_guncelle(self, admin_client, db_session):
        siparis = SiparisFactory.create(durum="Bekleme")

        response = admin_client.put(f"/api/siparisler/{siparis.id}", json={
            "durum": "Hazirlaniyor",
        })

        assert response.status_code == 200
        assert response.json()["durum"] == "Hazirlaniyor"

    def test_siparis_sil(self, admin_client, db_session):
        siparis = SiparisFactory.create()

        response = admin_client.delete(f"/api/siparisler/{siparis.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_siparis_olustur_gecmis_tarih(self, admin_client, db_session):
        """Geçmiş teslimat tarihi geçersiz — 422."""
        urun = UrunFactory.create()
        gecmis = (date.today() - timedelta(days=1)).isoformat()

        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": "Test",
            "teslimat_adresi": "Adres",
            "teslimat_tarihi": gecmis,
            "kalemler": [{"urun_id": urun.id, "miktar": 1, "birim_fiyat": 10.0}],
        })

        assert response.status_code == 422

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/siparisler/")
        assert response.status_code == 401

    def test_depocu_erisim_yasak(self, depocu_client):
        """Depocu siparişlere erişememeli — 403."""
        response = depocu_client.get("/api/siparisler/")
        assert response.status_code == 403
