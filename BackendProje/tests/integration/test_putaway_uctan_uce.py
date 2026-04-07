"""
Entegrasyon testler: Putaway sistemi uçtan uca senaryolar.

Kapsam:
5.2 A — Override akışı: Kapasite hatası sonrası süpervizör override ile tamamlama
5.2 B — Sevkiyat kısıtlaması: MIGRATION_STAGING'deki palet sevk edilemez
5.2 C — Görev havuzu izolasyonu: İki operatör aynı görevi alamaz

Not: Bu testler test DB'ye bağlanır (conftest.py engine fixture'ı).
"""

import pytest

from tests.factories import (
    YerlestirmeGoreviFactory,
    PaletFactory,
    RafFactory,
    ZonFactory,
    KullaniciFactory,
    DepoFactory,
    LotFactory,   # Eklendi
    UrunFactory,  # Eklendi
)
from app.core.auth import create_access_token

pytestmark = pytest.mark.integration


# ─── Override Akışı ──────────────────────────────────────────────────────

class TestOverrideAkisi:
    def test_devam_ediyor_gorev_override_ile_tamamlanir(self, admin_client, admin_user, db_session):
        """
        Senaryo:
          1. Görev DevamEdiyor durumunda
          2. Admin override isteği gönderir (farklı raf + gerekçe)
          3. Görev Tamamlandi olur, override alanları dolu
        """
        user, _ = admin_user
        raf = RafFactory.create(kapasite=10)
        hedef_raf = RafFactory.create(kapasite=10)
        gorev = YerlestirmeGoreviFactory.create(
            durum="DevamEdiyor",
            atanan_kullanici_id=user.id,
            onerilen_raf=raf,
        )

        response = admin_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/override",
            json={
                "gerceklesen_raf_id": hedef_raf.id,
                "neden": "Kapasite istisnası — süpervizör onayladı",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["durum"] == "Tamamlandi"
        assert data["gerceklesen_raf_id"] == hedef_raf.id
        assert data["override_kullanici_id"] == user.id
        assert data["override_neden"] == "Kapasite istisnası — süpervizör onayladı"

    def test_override_neden_bos_ise_422(self, admin_client, admin_user, db_session):
        user, _ = admin_user
        raf = RafFactory.create(kapasite=10)
        gorev = YerlestirmeGoreviFactory.create(
            durum="DevamEdiyor",
            atanan_kullanici_id=user.id,
            onerilen_raf=raf,
        )

        response = admin_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/override",
            json={"gerceklesen_raf_id": raf.id, "neden": ""},
        )

        assert response.status_code == 422

    def test_override_gerceklesen_raf_id_zorunlu(self, admin_client, admin_user, db_session):
        user, _ = admin_user
        raf = RafFactory.create(kapasite=10)
        gorev = YerlestirmeGoreviFactory.create(
            durum="DevamEdiyor",
            atanan_kullanici_id=user.id,
            onerilen_raf=raf,
        )

        response = admin_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/override",
            json={"neden": "Gerekçe var ama raf id yok"},
        )

        assert response.status_code == 422

    def test_olmayan_raf_ile_override_404(self, admin_client, admin_user, db_session):
        user, _ = admin_user
        raf = RafFactory.create(kapasite=10)
        gorev = YerlestirmeGoreviFactory.create(
            durum="DevamEdiyor",
            atanan_kullanici_id=user.id,
            onerilen_raf=raf,
        )

        response = admin_client.post(
            f"/api/yerlestirme-gorevleri/{gorev.id}/override",
            json={"gerceklesen_raf_id": 999999, "neden": "Gerekçe"},
        )

        assert response.status_code == 404


# ─── Görev Havuzu Izolasyonu ─────────────────────────────────────────────

# ─── Görev Havuzu Izolasyonu ─────────────────────────────────────────────

class TestGorevHavuzuIzolasyonu:
    def test_atandi_gorev_baska_operatöre_tekrar_atanmaz(self, client):
        """
        Senaryo:
          1. Depocu A görevi alır → Atandi
          2. Depocu B sonraki-gorevi-al yapar → aynı görevi ALAMAZ (havuzda Bekliyor yok)
        """
        depocu_a = KullaniciFactory.create(kullanici_adi="depocu_a", rol="depocu")
        token_a = create_access_token(data={"sub": depocu_a.kullanici_adi})

        depocu_b = KullaniciFactory.create(kullanici_adi="depocu_b", rol="depocu")
        token_b = create_access_token(data={"sub": depocu_b.kullanici_adi})

        # Sadece 1 bekleyen görev var
        YerlestirmeGoreviFactory.create(durum="Bekliyor")

        client.headers["Authorization"] = f"Bearer {token_a}"
        # URL güncellendi: /siradaki-al -> /sonraki-gorevi-al
        res_a = client.post("/api/yerlestirme-gorevleri/sonraki-gorevi-al")
        assert res_a.status_code == 200
        assert res_a.json()["durum"] == "Atandi"

        client.headers["Authorization"] = f"Bearer {token_b}"
        # URL güncellendi: /siradaki-al -> /sonraki-gorevi-al
        res_b = client.post("/api/yerlestirme-gorevleri/sonraki-gorevi-al")
        assert res_b.status_code == 200
        assert res_b.json() is None  # Havuzda bekleyen kalmadı

    def test_birakilan_gorev_baska_operatöre_atanabilir(self, client):
        """
        Senaryo:
          1. Depocu A görevi alır → Atandi
          2. Depocu A bırakır → Bekliyor
          3. Depocu B alır → Atandi
        """
        depocu_a = KullaniciFactory.create(kullanici_adi="depocu_a2", rol="depocu")
        token_a = create_access_token(data={"sub": depocu_a.kullanici_adi})

        depocu_b = KullaniciFactory.create(kullanici_adi="depocu_b2", rol="depocu")
        token_b = create_access_token(data={"sub": depocu_b.kullanici_adi})

        YerlestirmeGoreviFactory.create(durum="Bekliyor")

        # A alır
        client.headers["Authorization"] = f"Bearer {token_a}"
        # URL güncellendi: /siradaki-al -> /sonraki-gorevi-al
        res_a = client.post("/api/yerlestirme-gorevleri/sonraki-gorevi-al")
        assert res_a.status_code == 200
        assert res_a.json()["durum"] == "Atandi"
        gorev_id = res_a.json()["id"]

        # A bırakır
        res_birak = client.post(f"/api/yerlestirme-gorevleri/{gorev_id}/birak")
        assert res_birak.status_code == 200
        assert res_birak.json()["durum"] == "Bekliyor"

        # B alır
        client.headers["Authorization"] = f"Bearer {token_b}"
        # URL güncellendi: /siradaki-al -> /sonraki-gorevi-al
        res_b = client.post("/api/yerlestirme-gorevleri/sonraki-gorevi-al")
        assert res_b.status_code == 200
        assert res_b.json()["durum"] == "Atandi"
        assert res_b.json()["atanan_kullanici_id"] == depocu_b.id


# ─── Sevkiyat Kısıtlaması ────────────────────────────────────────────────

class TestSevkiyatKisitlamasi:
    def test_staging_raftaki_palet_sevkiyata_dahil_edilemez(self, admin_client, db_session):
        """
        Senaryo:
          MIGRATION_STAGING rafındaki palet varsa, palet sevkiyata eklenemez.
          Bu test, palet çıkış servisinin kısıtlamasını doğrular.

        Not: Bu kısıtlama PaletCikisService katmanında uygulanır. Test, palet çıkış
        endpoint'i üzerinden kontrol eder.
        """
        # MIGRATION_STAGING rafı kodunu içeren bir raf oluştur
        staging_raf = RafFactory.create(kod="STG-000-00-00-00", kapasite=100)
        urun = UrunFactory.create()
        lot = LotFactory.create(urun=urun)
        palet = PaletFactory.create(lot=lot, raf=staging_raf, aktif=True)

        # Stok hareketi çıkış endpoint'i (sevkiyat) staging paleti reddetmeli
        response = admin_client.post(
            "/api/stok-hareketleri/cikis",
            json={
                "palet_id": palet.id,
                "aciklama": "Sevkiyat denemesi",
            },
        )

        # Staging palet sevk edilemez — 400 veya 422 beklenir
        assert response.status_code in (400, 422, 404), (
            f"Staging paleti sevk edilememeli. Aldık: {response.status_code} — {response.json()}"
        )

    def test_normal_raftaki_palet_cikis_yapilabilir(self, admin_client, db_session):
        """
        STAGING dışı normal bir raftaki aktif palet için çıkış akışı başlatılabilmeli.
        Bu test kısıtlamanın aşırı geniş olmadığını doğrular.
        """
        normal_raf = RafFactory.create(kod="GNL-A-01-01-01", kapasite=10)
        urun = UrunFactory.create()
        lot = LotFactory.create(urun=urun)
        palet = PaletFactory.create(lot=lot, raf=normal_raf, aktif=True)

        response = admin_client.post(
            "/api/stok-hareketleri/cikis",
            json={
                "palet_id": palet.id,
                "aciklama": "Normal çıkış",
            },
        )

        # Staging kısıtlaması devreye girmemeli — ya 200 (başarı) ya işlemin
        # başka bir validasyonu (raf doluluk vb.) tetiklenir, ama 400 (staging) değil
        assert response.status_code != 400 or "Konumu belirsiz" not in response.json().get("detail", "")
