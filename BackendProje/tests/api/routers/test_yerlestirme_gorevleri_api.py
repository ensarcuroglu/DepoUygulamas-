"""
API testler: Yerleştirme Görevleri endpoint'leri.

Kapsam:
- GET /api/yerlestirme-gorevleri/  — listeleme
- GET /api/yerlestirme-gorevleri/{id}  — detay
- GET /api/yerlestirme-gorevleri/bekleyen/ozet  — özet istatistik
- POST /api/yerlestirme-gorevleri/siradaki-al  — FIFO pull
- POST /api/yerlestirme-gorevleri/{id}/baslat  — Atandi → DevamEdiyor
- POST /api/yerlestirme-gorevleri/{id}/birak  — Atandi → Bekliyor
- POST /api/yerlestirme-gorevleri/{id}/iptal  — admin iptal
- Rol erişim kontrolleri
"""

import pytest

from tests.factories import YerlestirmeGoreviFactory, PaletFactory, RafFactory, KullaniciFactory
from app.core.auth import create_access_token

pytestmark = pytest.mark.api


class TestYerlestirmeGorevleriListele:
    def test_bos_liste(self, admin_client, db_session):
        response = admin_client.get("/api/yerlestirme-gorevleri/")
        assert response.status_code == 200
        assert response.json() == []

    def test_gorev_listele(self, admin_client, db_session):
        YerlestirmeGoreviFactory.create(durum="Bekliyor")
        YerlestirmeGoreviFactory.create(durum="Bekliyor")

        response = admin_client.get("/api/yerlestirme-gorevleri/")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_durum_filtreleme(self, admin_client, db_session):
        YerlestirmeGoreviFactory.create(durum="Bekliyor")
        YerlestirmeGoreviFactory.create(durum="Tamamlandi")

        response = admin_client.get("/api/yerlestirme-gorevleri/?durum=Bekliyor")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["durum"] == "Bekliyor"

    def test_yetkisiz_erisim_401(self, client, db_session):
        response = client.get("/api/yerlestirme-gorevleri/")
        assert response.status_code == 401

    def test_depocu_listede_gorebilir(self, depocu_client, db_session):
        YerlestirmeGoreviFactory.create(durum="Bekliyor")
        response = depocu_client.get("/api/yerlestirme-gorevleri/")
        assert response.status_code == 200


class TestYerlestirmeGorevDetay:
    def test_mevcut_gorev_getirir(self, admin_client, db_session):
        gorev = YerlestirmeGoreviFactory.create(durum="Bekliyor")

        response = admin_client.get(f"/api/yerlestirme-gorevleri/{gorev.id}")

        assert response.status_code == 200
        assert response.json()["id"] == gorev.id
        assert response.json()["durum"] == "Bekliyor"

    def test_olmayan_gorev_404(self, admin_client, db_session):
        response = admin_client.get("/api/yerlestirme-gorevleri/99999")
        assert response.status_code == 404


class TestBekleyenOzet:
    def test_ozet_bekliyor_sayar(self, admin_client, db_session):
        YerlestirmeGoreviFactory.create(durum="Bekliyor", oncelik=1)  # acil
        YerlestirmeGoreviFactory.create(durum="Bekliyor", oncelik=5)  # normal
        YerlestirmeGoreviFactory.create(durum="Tamamlandi")           # sayılmamalı

        response = admin_client.get("/api/yerlestirme-gorevleri/bekleyen/ozet")

        assert response.status_code == 200
        data = response.json()
        assert data["toplam_bekleyen"] == 2
        assert data["acil"] == 1

    def test_bos_depoda_sifir(self, admin_client, db_session):
        response = admin_client.get("/api/yerlestirme-gorevleri/bekleyen/ozet")
        assert response.status_code == 200
        assert response.json()["toplam_bekleyen"] == 0


class TestSiradakiGoreviAl:
    def test_bekleyen_gorev_yoksa_none(self, depocu_client, db_session):
        response = depocu_client.post("/api/yerlestirme-gorevleri/siradaki-al")
        assert response.status_code == 200
        assert response.json() is None

    def test_bekleyen_gorev_varsa_atandi(self, depocu_client, depocu_user, db_session):
        YerlestirmeGoreviFactory.create(durum="Bekliyor", oncelik=5)

        response = depocu_client.post("/api/yerlestirme-gorevleri/siradaki-al")

        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["durum"] == "Atandi"
        user, _ = depocu_user
        assert data["atanan_kullanici_id"] == user.id

    def test_oncelik_sirasi_korunur(self, depocu_client, db_session):
        """Önce acil (oncelik=1) görevi almalı."""
        YerlestirmeGoreviFactory.create(durum="Bekliyor", oncelik=5)
        YerlestirmeGoreviFactory.create(durum="Bekliyor", oncelik=1)

        response = depocu_client.post("/api/yerlestirme-gorevleri/siradaki-al")

        assert response.status_code == 200
        assert response.json()["oncelik"] == 1

    def test_admin_de_alabilir(self, admin_client, db_session):
        YerlestirmeGoreviFactory.create(durum="Bekliyor")
        response = admin_client.post("/api/yerlestirme-gorevleri/siradaki-al")
        assert response.status_code == 200


class TestGorevBaslat:
    def test_atandi_gorev_devam_ediyor_olur(self, depocu_client, depocu_user, db_session):
        user, _ = depocu_user
        gorev = YerlestirmeGoreviFactory.create(
            durum="Atandi", atanan_kullanici_id=user.id
        )

        response = depocu_client.post(f"/api/yerlestirme-gorevleri/{gorev.id}/baslat")

        assert response.status_code == 200
        assert response.json()["durum"] == "DevamEdiyor"

    def test_baska_operatörün_gorevi_baslatamaz(self, depocu_client, db_session):
        """Görevi başka biri almışsa, bu depocu başlatamaz."""
        baska_kullanici = KullaniciFactory.create(kullanici_adi="baska_depocu", rol="depocu")
        gorev = YerlestirmeGoreviFactory.create(
            durum="Atandi", atanan_kullanici_id=baska_kullanici.id
        )

        response = depocu_client.post(f"/api/yerlestirme-gorevleri/{gorev.id}/baslat")

        assert response.status_code in (400, 403, 422)

    def test_bekliyor_gorev_baslatilamaz(self, depocu_client, db_session):
        """Atanmamış görev (Bekliyor) doğrudan başlatılamaz — geçersiz durum geçişi."""
        gorev = YerlestirmeGoreviFactory.create(durum="Bekliyor")

        response = depocu_client.post(f"/api/yerlestirme-gorevleri/{gorev.id}/baslat")

        assert response.status_code in (400, 422)


class TestGoreviBirak:
    def test_atandi_gorev_havuza_iade_edilir(self, depocu_client, depocu_user, db_session):
        user, _ = depocu_user
        gorev = YerlestirmeGoreviFactory.create(
            durum="Atandi", atanan_kullanici_id=user.id
        )

        response = depocu_client.post(f"/api/yerlestirme-gorevleri/{gorev.id}/birak")

        assert response.status_code == 200
        assert response.json()["durum"] == "Bekliyor"
        assert response.json()["atanan_kullanici_id"] is None

    def test_bekliyor_gorev_birakilamaz(self, depocu_client, depocu_user, db_session):
        user, _ = depocu_user
        gorev = YerlestirmeGoreviFactory.create(durum="Bekliyor")

        response = depocu_client.post(f"/api/yerlestirme-gorevleri/{gorev.id}/birak")

        assert response.status_code in (400, 422)


class TestGorevIptal:
    def test_admin_bekliyor_gorevi_iptal_edebilir(self, admin_client, db_session):
        gorev = YerlestirmeGoreviFactory.create(durum="Bekliyor")

        response = admin_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/iptal",
            json={"neden": "Test iptali"},
        )

        assert response.status_code == 200
        assert response.json()["durum"] == "IptalEdildi"

    def test_iptal_nedeni_zorunlu(self, admin_client, db_session):
        gorev = YerlestirmeGoreviFactory.create(durum="Bekliyor")

        response = admin_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/iptal",
            json={},
        )

        assert response.status_code == 422

    def test_tamamlandi_gorev_iptal_edilemez(self, admin_client, db_session):
        gorev = YerlestirmeGoreviFactory.create(durum="Tamamlandi")

        response = admin_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/iptal",
            json={"neden": "Geç iptal"},
        )

        assert response.status_code in (400, 422)

    def test_depocu_admin_endpointine_erisemez(self, depocu_client, db_session):
        gorev = YerlestirmeGoreviFactory.create(durum="Bekliyor")

        response = depocu_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/iptal",
            json={"neden": "Yetkisiz iptal"},
        )

        assert response.status_code == 403
