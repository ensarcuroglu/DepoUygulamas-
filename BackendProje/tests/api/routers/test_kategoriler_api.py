"""
API testler: Kategoriler endpoint'leri — sadece admin erişimi.
"""

import pytest
from tests.factories import KategoriFactory

pytestmark = pytest.mark.api


class TestKategoriEndpoints:
    """Kategori CRUD endpoint testleri."""

    def test_kategori_listele(self, admin_client, db_session):
        KategoriFactory.create(isim="Elektronik")
        KategoriFactory.create(isim="Gıda")

        response = admin_client.get("/api/kategoriler/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_kategori_olustur(self, admin_client):
        response = admin_client.post("/api/kategoriler/", json={
            "isim": "Yeni Kategori",
            "aciklama": "Test açıklama",
            "ikon": "FolderOpen",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["isim"] == "Yeni Kategori"
        assert data["aktif"] is True

    def test_kategori_getir(self, admin_client, db_session):
        kategori = KategoriFactory.create(isim="Araç Gereç")

        response = admin_client.get(f"/api/kategoriler/{kategori.id}")

        assert response.status_code == 200
        assert response.json()["isim"] == "Araç Gereç"

    def test_kategori_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/kategoriler/99999")
        assert response.status_code == 404

    def test_kategori_guncelle(self, admin_client, db_session):
        kategori = KategoriFactory.create(isim="Eski Isim")

        response = admin_client.put(f"/api/kategoriler/{kategori.id}", json={
            "isim": "Yeni Isim",
        })

        assert response.status_code == 200
        assert response.json()["isim"] == "Yeni Isim"

    def test_kategori_sil(self, admin_client, db_session):
        kategori = KategoriFactory.create()

        response = admin_client.delete(f"/api/kategoriler/{kategori.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/kategoriler/")
        assert response.status_code == 401

    def test_depocu_erisim_yasak(self, depocu_client):
        """Depocu kategori listeleyememeli — 403."""
        response = depocu_client.get("/api/kategoriler/")
        assert response.status_code == 403
