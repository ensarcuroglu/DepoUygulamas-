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


class TestSiparisSinirDegerleri:
    """
    API katmanı sipariş sınır değeri testleri — Pydantic 422 doğrulama.
    """

    @pytest.mark.parametrize("musteri_adi", ["", "   "])
    def test_bos_musteri_adi_422(self, admin_client, db_session, musteri_adi):
        """Boş/boşluklu müşteri adı 422 döndürmeli."""
        urun = UrunFactory.create()
        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": musteri_adi,
            "teslimat_adresi": "Test Adres",
            "teslimat_tarihi": _gelecek_tarih(),
            "kalemler": [{"urun_id": urun.id, "miktar": 1, "birim_fiyat": 10.0}],
        })
        assert response.status_code == 422

    def test_bos_kalemler_listesi_422(self, admin_client):
        """Kalem listesi boş olamaz — 422."""
        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": "Test",
            "teslimat_adresi": "Adres",
            "teslimat_tarihi": _gelecek_tarih(),
            "kalemler": [],
        })
        assert response.status_code == 422

    def test_duplicate_urun_id_422(self, admin_client, db_session):
        """Aynı ürün iki kalemde yer alamaz — 422."""
        urun = UrunFactory.create()
        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": "Test",
            "teslimat_adresi": "Adres",
            "teslimat_tarihi": _gelecek_tarih(),
            "kalemler": [
                {"urun_id": urun.id, "miktar": 2, "birim_fiyat": 10.0},
                {"urun_id": urun.id, "miktar": 3, "birim_fiyat": 10.0},
            ],
        })
        assert response.status_code == 422

    def test_kalem_miktar_sifir_422(self, admin_client, db_session):
        """Kalem miktarı 0 olamaz — 422."""
        urun = UrunFactory.create()
        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": "Test",
            "teslimat_adresi": "Adres",
            "teslimat_tarihi": _gelecek_tarih(),
            "kalemler": [{"urun_id": urun.id, "miktar": 0, "birim_fiyat": 10.0}],
        })
        assert response.status_code == 422

    def test_kalem_birim_fiyat_negatif_422(self, admin_client, db_session):
        """Negatif birim fiyat 422 döndürmeli."""
        urun = UrunFactory.create()
        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": "Test",
            "teslimat_adresi": "Adres",
            "teslimat_tarihi": _gelecek_tarih(),
            "kalemler": [{"urun_id": urun.id, "miktar": 1, "birim_fiyat": -5.0}],
        })
        assert response.status_code == 422

    def test_musteri_adi_max_uzunluk_asimi_422(self, admin_client):
        """201 karakterlik müşteri adı 422 döndürmeli."""
        response = admin_client.post("/api/siparisler/", json={
            "musteri_adi": "x" * 201,
            "teslimat_adresi": "Adres",
            "teslimat_tarihi": _gelecek_tarih(),
            "kalemler": [{"urun_id": 1, "miktar": 1, "birim_fiyat": 10.0}],
        })
        assert response.status_code == 422


class TestSiparisDurumGecisi:
    """
    Sipariş durum makinesi geçiş kombinasyonları.

    Geçerli geçişler  → HTTP 200
    Geçersiz geçişler → HTTP 400  (GecersizDurumGecisiError)

    Durum grafiği:
      Bekleme ──► Hazirlaniyor ──► YolaCikti ──► TeslimEdildi
          └────────────────────────────────────► Iptal
                         └──────────────────────► Iptal
    """

    @pytest.mark.parametrize("baslangic,hedef,beklenen", [
        # --- Geçerli geçişler ---
        ("Bekleme",      "Hazirlaniyor",  200),
        ("Bekleme",      "Iptal",         200),
        ("Hazirlaniyor", "YolaCikti",     200),
        ("Hazirlaniyor", "Iptal",         200),
        ("YolaCikti",    "TeslimEdildi",  200),
        # --- Geçersiz geçişler ---
        ("Bekleme",      "TeslimEdildi",  400),  # Atlama
        ("Bekleme",      "YolaCikti",     400),  # Atlama
        ("TeslimEdildi", "Bekleme",       400),  # Geri
        ("Iptal",        "Bekleme",       400),  # İptal geri alınamaz
        ("Hazirlaniyor", "Bekleme",       400),  # Geri
    ])
    def test_siparis_durum_gecisi(self, admin_client, db_session, baslangic, hedef, beklenen):
        siparis = SiparisFactory.create(durum=baslangic)
        response = admin_client.put(f"/api/siparisler/{siparis.id}", json={"durum": hedef})
        assert response.status_code == beklenen
