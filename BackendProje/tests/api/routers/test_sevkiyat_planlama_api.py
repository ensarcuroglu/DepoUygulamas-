"""
API testler: Sevkiyat Planlama endpoint'leri — admin + lojistik erişimi.
"""

import pytest
from datetime import date, timedelta
from tests.factories import SevkiyatPlaniFactory, SiparisFactory

pytestmark = pytest.mark.api


class TestSevkiyatPlaniEndpoints:
    """Sevkiyat Planı CRUD endpoint testleri."""

    def test_sevkiyat_listele(self, admin_client, db_session):
        SevkiyatPlaniFactory.create()
        SevkiyatPlaniFactory.create()

        response = admin_client.get("/api/sevkiyat-planlama/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_sevkiyat_listele_lojistik(self, lojistik_client, db_session):
        SevkiyatPlaniFactory.create()

        response = lojistik_client.get("/api/sevkiyat-planlama/")

        assert response.status_code == 200

    def test_sevkiyat_listele_durum_filtresi(self, admin_client, db_session):
        SevkiyatPlaniFactory.create(durum="Planlandi")
        SevkiyatPlaniFactory.create(durum="Yukleniyor")

        response = admin_client.get("/api/sevkiyat-planlama/?durum=Planlandi")

        assert response.status_code == 200
        data = response.json()
        assert all(p["durum"] == "Planlandi" for p in data)

    def test_sevkiyat_olustur(self, admin_client, db_session):
        siparis = SiparisFactory.create()

        response = admin_client.post("/api/sevkiyat-planlama/", json={
            "siparis_id": siparis.id,
            "tir_plaka": "34 TES 001",
            "sofor_adi": "Test Şoför",
            "sofor_telefon": "05551112233",
            "depo_kapi": "Kapi-1",
            "yukleme_tarihi": (date.today() + timedelta(days=1)).isoformat(),
            "durum": "Planlandi",
        })

        assert response.status_code == 201
        data = response.json()
        assert data["siparis_id"] == siparis.id
        assert data["durum"] == "Planlandi"

    def test_sevkiyat_olustur_lojistik(self, lojistik_client, db_session):
        siparis = SiparisFactory.create()

        response = lojistik_client.post("/api/sevkiyat-planlama/", json={
            "siparis_id": siparis.id,
            "yukleme_tarihi": (date.today() + timedelta(days=1)).isoformat(),
            "durum": "Planlandi",
        })

        assert response.status_code == 201

    def test_sevkiyat_getir(self, admin_client, db_session):
        plan = SevkiyatPlaniFactory.create(tir_plaka="34 ABC 999")

        response = admin_client.get(f"/api/sevkiyat-planlama/{plan.id}")

        assert response.status_code == 200
        assert response.json()["tir_plaka"] == "34 ABC 999"

    def test_sevkiyat_getir_bulunamadi(self, admin_client):
        response = admin_client.get("/api/sevkiyat-planlama/99999")
        assert response.status_code == 404

    def test_sevkiyat_guncelle(self, admin_client, db_session):
        plan = SevkiyatPlaniFactory.create(durum="Planlandi")

        response = admin_client.put(f"/api/sevkiyat-planlama/{plan.id}", json={
            "durum": "Yukleniyor",
        })

        assert response.status_code == 200
        assert response.json()["durum"] == "Yukleniyor"

    def test_sevkiyat_sil(self, admin_client, db_session):
        plan = SevkiyatPlaniFactory.create()

        response = admin_client.delete(f"/api/sevkiyat-planlama/{plan.id}")

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_sevkiyat_sil_lojistik_yasak(self, lojistik_client, db_session):
        """Lojistik kullanıcı sevkiyat planı silemez — 403."""
        plan = SevkiyatPlaniFactory.create()

        response = lojistik_client.delete(f"/api/sevkiyat-planlama/{plan.id}")

        assert response.status_code == 403

    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/sevkiyat-planlama/")
        assert response.status_code == 401

    def test_depocu_erisim_yasak(self, depocu_client):
        """Depocu sevkiyat planlarına erişememeli — 403."""
        response = depocu_client.get("/api/sevkiyat-planlama/")
        assert response.status_code == 403


class TestSevkiyatDurumGecisi:
    """
    Sevkiyat planı durum makinesi geçiş kombinasyonları.

    Geçerli geçişler  → HTTP 200
    Geçersiz geçişler → HTTP 400  (GecersizDurumGecisiError)

    Not: Planlandi → Yukleniyor geçişi FIFO stok çıkışı tetikler;
    bu senaryo test_sevkiyat_guncelle ile ayrıca test edilmektedir.
    Aşağıdaki parametrize stok bağımlılığı olmayan geçişleri kapsar.

    Durum grafiği:
      Planlandi ──► Yukleniyor ──► Yolda ──► TeslimEdildi
    """

    @pytest.mark.parametrize("baslangic,hedef,beklenen", [
        # --- Geçerli geçişler (stok bağımlılığı yok) ---
        ("Yukleniyor", "Yolda",         200),
        ("Yolda",      "TeslimEdildi",  200),
        # --- Geçersiz geçişler ---
        ("Planlandi",    "TeslimEdildi", 400),  # Atlama
        ("Planlandi",    "Yolda",        400),  # Atlama
        ("TeslimEdildi", "Planlandi",    400),  # Geri
        ("Yukleniyor",   "Planlandi",    400),  # Geri
        ("Yolda",        "Planlandi",    400),  # Geri
        ("Yolda",        "Yukleniyor",   400),  # Geri
    ])
    def test_sevkiyat_durum_gecisi(self, admin_client, db_session, baslangic, hedef, beklenen):
        plan = SevkiyatPlaniFactory.create(durum=baslangic)
        response = admin_client.put(f"/api/sevkiyat-planlama/{plan.id}", json={"durum": hedef})
        assert response.status_code == beklenen
