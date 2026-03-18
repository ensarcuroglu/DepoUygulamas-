"""
API testler: Urunler endpoint'leri — tam HTTP döngüsü.
Legacy router (/api/urunler) üzerinden test eder.
"""

import pytest
from tests.factories import UrunFactory, KategoriFactory, MarkaFactory

pytestmark = pytest.mark.api


class TestUrunListele:
    """GET /api/urunler/ testleri."""

    def test_yetkisiz_erisim(self, client):
        """Token olmadan 401."""
        response = client.get("/api/urunler/")
        assert response.status_code == 401

    def test_bos_liste(self, admin_client):
        """Ürün yokken boş liste dönmeli."""
        response = admin_client.get("/api/urunler/")
        assert response.status_code == 200
        assert response.json() == []

    def test_urun_listeleme(self, admin_client, db_session):
        """Ürünler listelenebilmeli."""
        UrunFactory.create(isim="Ürün A")
        UrunFactory.create(isim="Ürün B")

        response = admin_client.get("/api/urunler/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_arama_filtresi(self, admin_client, db_session):
        """Search parametresi ile arama."""
        UrunFactory.create(isim="Elma Suyu")
        UrunFactory.create(isim="Çikolata")

        response = admin_client.get("/api/urunler/", params={"search": "Elma"})

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["isim"] == "Elma Suyu"


class TestUrunOlustur:
    """POST /api/urunler/ testleri."""

    def test_basarili_olusturma(self, admin_client, db_session):
        """Admin yeni ürün oluşturabilmeli."""
        kat = KategoriFactory.create()
        marka = MarkaFactory.create()

        response = admin_client.post("/api/urunler/", json={
            "isim": "API Test Ürün",
            "barkod": "5555555555555",
            "kategori_id": kat.id,
            "marka_id": marka.id,
            "birim": "Adet",
            "fiyat": 49.90,
            "min_stok": 10,
        })

        assert response.status_code == 201
        data = response.json()
        assert data["isim"] == "API Test Ürün"
        assert data["fiyat"] == 49.90

    def test_gecersiz_barkod(self, admin_client):
        """Geçersiz barkod formatı ile 422 dönmeli."""
        response = admin_client.post("/api/urunler/", json={
            "isim": "Test",
            "barkod": "ABC",
        })

        assert response.status_code == 422


class TestUrunGetir:
    """GET /api/urunler/{id} testleri."""

    def test_basarili_getir(self, admin_client, db_session):
        """ID ile ürün getirme."""
        urun = UrunFactory.create(isim="Detay Ürün")

        response = admin_client.get(f"/api/urunler/{urun.id}")

        assert response.status_code == 200
        assert response.json()["isim"] == "Detay Ürün"

    def test_olmayan_urun(self, admin_client):
        """Olmayan ürün için 404 dönmeli."""
        response = admin_client.get("/api/urunler/99999")

        assert response.status_code == 404
