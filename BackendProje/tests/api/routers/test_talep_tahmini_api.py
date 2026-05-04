from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pytest

from tests.factories import LotFactory, PaletFactory, StokHareketiFactory, UrunFactory

pytestmark = pytest.mark.api


def _hareket_tarihi(days_ago: int) -> datetime:
    return datetime.combine(date.today() - timedelta(days=days_ago), time(hour=10))


def _cikis_ekle(urun, days_ago: int, miktar: int = 1):
    return StokHareketiFactory.create(
        urun=urun,
        hareket_tipi="cikis",
        miktar=miktar,
        tarih=_hareket_tarihi(days_ago),
    )


def _stok_ekle(urun, miktar: int):
    lot = LotFactory.create(urun=urun)
    return PaletFactory.create(lot=lot, koli_adedi=miktar, aktif=True)


def _stabil_cikis_gecmisi_ekle(urun, miktar: int = 1):
    for days_ago in range(30):
        _cikis_ekle(urun, days_ago=days_ago, miktar=miktar)


class TestTalepTahminiYetki:
    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/talep-tahmini/urunler")
        assert response.status_code == 401

    def test_depocu_erisim_yasak(self, depocu_client):
        response = depocu_client.get("/api/talep-tahmini/urunler")
        assert response.status_code == 403

    def test_admin_urunleri_listeleyebilir(self, admin_client):
        UrunFactory.create(isim="Talep A")

        response = admin_client.get("/api/talep-tahmini/urunler")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["isim"] == "Talep A"

    def test_lojistik_urunleri_listeleyebilir(self, lojistik_client):
        UrunFactory.create(isim="Talep Lojistik")

        response = lojistik_client.get("/api/talep-tahmini/urunler")

        assert response.status_code == 200
        assert response.json()[0]["isim"] == "Talep Lojistik"


class TestTalepTahminiHesaplama:
    def test_stok_cikislari_gunluk_aggregate_edilir(self, admin_client):
        urun = UrunFactory.create(isim="Aggregate Urun")
        hedef_tarih = date.today() - timedelta(days=2)
        _cikis_ekle(urun, days_ago=2, miktar=3)
        _cikis_ekle(urun, days_ago=2, miktar=4)
        StokHareketiFactory.create(
            urun=urun,
            hareket_tipi="giris",
            miktar=99,
            tarih=_hareket_tarihi(2),
        )

        response = admin_client.get(
            f"/api/talep-tahmini/urunler/{urun.id}",
            params={"tahmin_gun": 7},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data["gecmis_gunluk_seri"]) == 90
        assert len(data["gelecek_gunluk_tahmin"]) == 7
        gun = next(
            item for item in data["gecmis_gunluk_seri"]
            if item["tarih"] == hedef_tarih.isoformat()
        )
        assert gun["miktar"] == 7

    def test_gecmis_verisi_yoksa_cold_start_uyarisi_doner(self, admin_client):
        urun = UrunFactory.create(isim="Yeni Urun")

        response = admin_client.get(
            f"/api/talep-tahmini/urunler/{urun.id}",
            params={"tahmin_gun": 14},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["tahmini_talep"] == 0
        assert data["veri_guven_skoru"] == 0
        assert any("cold-start" in uyari for uyari in data["uyarilar"])

    def test_gecersiz_tahmin_gunu_422_doner(self, admin_client):
        urun = UrunFactory.create()

        response = admin_client.get(
            f"/api/talep-tahmini/urunler/{urun.id}",
            params={"tahmin_gun": 5},
        )

        assert response.status_code == 422

    @pytest.mark.parametrize(
        ("stok", "min_stok", "beklenen_risk"),
        [
            (0, 10, "kritik"),
            (15, 10, "dikkat"),
            (40, 10, "yok"),
        ],
    )
    def test_stok_riski_hesaplanir(
        self,
        admin_client,
        stok: int,
        min_stok: int,
        beklenen_risk: str,
    ):
        urun = UrunFactory.create(min_stok=min_stok)
        if stok > 0:
            _stok_ekle(urun, stok)
        _stabil_cikis_gecmisi_ekle(urun, miktar=1)

        response = admin_client.get(
            f"/api/talep-tahmini/urunler/{urun.id}",
            params={"tahmin_gun": 7},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["stok_riski"] == beklenen_risk

    def test_response_confidence_band_alanlari_iceriyor(self, admin_client):
        urun = UrunFactory.create(min_stok=10)
        _stok_ekle(urun, 50)
        _stabil_cikis_gecmisi_ekle(urun, miktar=1)

        response = admin_client.get(
            f"/api/talep-tahmini/urunler/{urun.id}",
            params={"tahmin_gun": 7},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert "model_versiyonu" in data
        assert isinstance(data["gelecek_gunluk_tahmin"], list)
        assert len(data["gelecek_gunluk_tahmin"]) == 7
        ilk = data["gelecek_gunluk_tahmin"][0]
        assert "alt_sinir" in ilk and "ust_sinir" in ilk
        assert ilk["alt_sinir"] <= ilk["tahmin"] <= ilk["ust_sinir"]


class TestRiskliUrunlerEndpoint:
    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/talep-tahmini/riskli-urunler")
        assert response.status_code == 401

    def test_cache_bos_oldugunda_bos_liste_doner(self, admin_client):
        UrunFactory.create()
        response = admin_client.get(
            "/api/talep-tahmini/riskli-urunler",
            params={"tahmin_gun": 7},
        )
        assert response.status_code == 200
        assert response.json() == []

    def test_gecersiz_ufuk_422_doner(self, admin_client):
        response = admin_client.get(
            "/api/talep-tahmini/riskli-urunler",
            params={"tahmin_gun": 5},
        )
        assert response.status_code == 422

    def test_yazma_sonrasi_riskli_kayit_listelenir(self, admin_client, db_session):
        from app.core.repositories.talep_tahmini_repository import CacheKaydi
        from app.infrastructure.persistence.repositories import (
            SqlAlchemyTalepTahminCacheRepository,
        )

        urun = UrunFactory.create(isim="Riskli Urun", min_stok=10)
        cache_repo = SqlAlchemyTalepTahminCacheRepository(db_session)
        cache_repo.yaz(
            CacheKaydi(
                urun_id=urun.id,
                tahmin_gun=7,
                payload={
                    "tahmini_talep": 50.0,
                    "gunluk_ortalama_talep": 7.1,
                    "talep_sinyali": "yuksek",
                    "son_hesaplanma": "2026-05-04T02:00:00",
                },
                stok_riski="kritik",
                tahmini_talep=50.0,
                onerilen_ikmal=40.0,
                veri_guven_skoru=0.8,
                model_versiyonu="sklearn-gbr-quantile-1.0",
                hesaplanma_tarihi=date.today(),
            )
        )
        db_session.commit()

        response = admin_client.get(
            "/api/talep-tahmini/riskli-urunler",
            params={"tahmin_gun": 7},
        )

        assert response.status_code == 200, response.text
        data = response.json()
        assert len(data) == 1
        assert data[0]["urun"]["id"] == urun.id
        assert data[0]["stok_riski"] == "kritik"
        assert data[0]["onerilen_ikmal_miktari"] == 40.0


class TestBacktestOzetEndpoint:
    def test_yetkisiz_erisim(self, client):
        response = client.get("/api/talep-tahmini/backtest-ozet")
        assert response.status_code == 401

    def test_aktif_urun_yoksa_sifir_doner(self, admin_client):
        response = admin_client.get(
            "/api/talep-tahmini/backtest-ozet",
            params={"tahmin_gun": 7},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["urun_sayisi"] == 0
        assert data["mae"] == 0
        assert data["mape"] == 0

