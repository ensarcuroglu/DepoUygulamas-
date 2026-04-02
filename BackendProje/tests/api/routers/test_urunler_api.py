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

    def test_alfanumerik_barkod_olusturma(self, admin_client):
        """SKU formatındaki barkod (örn. ARB-001) kabul edilmeli."""
        response = admin_client.post("/api/urunler/", json={
            "isim": "SKU Test",
            "barkod": "ARB-001",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["barkod"] == "ARB-001"

    def test_gecersiz_barkod(self, admin_client):
        """Geçersiz barkod formatı ile 422 dönmeli."""
        response = admin_client.post("/api/urunler/", json={
            "isim": "Test",
            "barkod": "ABC",
        })

        assert response.status_code == 422

    def test_ean_bosluk_ve_tire_normalizasyonu(self, admin_client):
        """EAN alanında boşluk/tire varsa normalize edilip kaydedilmeli."""
        response = admin_client.post("/api/urunler/", json={
            "isim": "EAN Normalize",
            "ean": "869-7430 089416",
            "barkod": "EAN-001",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["ean"] == "8697430089416"


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


class TestUrunGuncelle:
    """PUT /api/urunler/{id} testleri."""

    def test_alfanumerik_barkod_korunurken_ean_guncelleme(self, admin_client, db_session):
        """Alfanümerik barkodlu üründe EAN güncellemesi başarılı olmalı."""
        urun = UrunFactory.create(isim="Guncelle Test", barkod="ARB-001", ean="8697430089416")

        response = admin_client.put(f"/api/urunler/{urun.id}", json={
            "ean": "8697430089767",
            "barkod": "ARB-001",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["ean"] == "8697430089767"
        assert data["barkod"] == "ARB-001"


class TestUrunSinirDegerleri:
    """
    API katmanı sınır değeri testleri — Pydantic 422 yanıtı doğrulama.
    DB'ye ulaşmadan validation aşamasında reddedilmeli.
    """

    @pytest.mark.parametrize("isim", ["", "   "])
    def test_bos_isim_422(self, admin_client, isim):
        """Boş/boşluklu isim HTTP 422 döndürmeli."""
        response = admin_client.post("/api/urunler/", json={"isim": isim})
        assert response.status_code == 422

    def test_isim_max_uzunluk_asimi_422(self, admin_client):
        """201 karakterlik isim 422 döndürmeli."""
        response = admin_client.post("/api/urunler/", json={"isim": "x" * 201})
        assert response.status_code == 422

    def test_fiyat_negatif_422(self, admin_client):
        """Negatif fiyat 422 döndürmeli."""
        response = admin_client.post("/api/urunler/", json={"isim": "Test", "fiyat": -1.0})
        assert response.status_code == 422

    def test_ic_adet_sifir_422(self, admin_client):
        """ic_adet=0 ile 422 döndürmeli."""
        response = admin_client.post("/api/urunler/", json={"isim": "Test", "ic_adet": 0})
        assert response.status_code == 422

    def test_gecersiz_birim_422(self, admin_client):
        """Geçersiz birim değeri 422 döndürmeli."""
        response = admin_client.post("/api/urunler/", json={"isim": "Test", "birim": "Ton"})
        assert response.status_code == 422

    def test_ean_cok_kisa_422(self, admin_client):
        """7 haneli EAN 422 döndürmeli."""
        response = admin_client.post("/api/urunler/", json={"isim": "Test", "ean": "1234567"})
        assert response.status_code == 422

    def test_marka_id_sifir_422(self, admin_client):
        """marka_id=0 (gt=0 ihlali) 422 döndürmeli."""
        response = admin_client.post("/api/urunler/", json={"isim": "Test", "marka_id": 0})
        assert response.status_code == 422

    def test_barkod_cakismasi_409(self, admin_client, db_session):
        """Mevcut barkodla ürün oluşturma 409 döndürmeli."""
        UrunFactory.create(barkod="9876543210123")

        response = admin_client.post("/api/urunler/", json={
            "isim": "Cakisan Urun",
            "barkod": "9876543210123",
        })

        assert response.status_code == 409
