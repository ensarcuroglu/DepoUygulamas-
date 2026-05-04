from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_models.talep_tahmin.application import PredictDemandUseCase
from ml_models.talep_tahmin.domain import DailyStockExit, InputFeatures
from ml_models.talep_tahmin.infrastructure import BaselineMovingAveragePredictor
from ml_models.talep_tahmin.infrastructure.data_sources import SyntheticDemandDataSource


def sahte_90_gunluk_cikis_verisi() -> list[DailyStockExit]:
    baslangic = date.today() - timedelta(days=89)
    seri: list[DailyStockExit] = []

    for index in range(90):
        tarih = baslangic + timedelta(days=index)
        hafta_sonu_etkisi = 2 if tarih.weekday() in (5, 6) else 0
        hafif_trend = index // 30
        miktar = 8 + hafta_sonu_etkisi + hafif_trend
        seri.append(DailyStockExit(tarih=tarih, miktar=miktar))

    return seri


def baseline_tahmin_payload() -> dict:
    features = InputFeatures(
        urun_id=1,
        stok_cikis_gecmisi=sahte_90_gunluk_cikis_verisi(),
        mevcut_stok=180,
        min_stok=40,
    )
    use_case = PredictDemandUseCase(BaselineMovingAveragePredictor())
    sonuc = use_case.execute(features, tahmin_gun=30)

    payload = sonuc.model_dump()
    return payload


def test_baseline_tahmin_dto_formati() -> None:
    payload = baseline_tahmin_payload()
    zorunlu_alanlar = {
        "urun_id",
        "tahmin_gun",
        "tahmini_talep",
        "gunluk_ortalama_talep",
        "onerilen_ikmal_miktari",
        "guvenli_stok",
        "stok_riski",
        "talep_sinyali",
        "veri_guven_skoru",
        "uyarilar",
        "gunluk_tahmin_serisi",
        "trend",
        "model_versiyonu",
        "son_hesaplanma",
    }
    assert zorunlu_alanlar.issubset(payload)
    assert payload["urun_id"] == 1
    assert payload["tahmin_gun"] == 30
    assert payload["tahmini_talep"] > 0
    assert payload["gunluk_ortalama_talep"] > 0
    assert payload["onerilen_ikmal_miktari"] >= 0
    assert payload["stok_riski"] in {"yok", "dikkat", "kritik"}
    assert payload["talep_sinyali"] in {"dusuk", "normal", "yuksek"}
    assert 0 <= payload["veri_guven_skoru"] <= 1
    assert isinstance(payload["uyarilar"], list)
    assert len(payload["gunluk_tahmin_serisi"]) == payload["tahmin_gun"]
    nokta = payload["gunluk_tahmin_serisi"][0]
    assert nokta["alt_sinir"] <= nokta["tahmin"] <= nokta["ust_sinir"]
    assert payload["trend"]["yon"] in {"pozitif", "negatif", "stabil"}
    assert payload["model_versiyonu"].startswith("baseline-ma")


def test_cold_start_dusuk_guvenle_calismali() -> None:
    features = InputFeatures(
        urun_id=2,
        stok_cikis_gecmisi=[],
        mevcut_stok=100,
        min_stok=20,
    )
    sonuc = PredictDemandUseCase(BaselineMovingAveragePredictor()).execute(features)

    assert sonuc.urun_id == 2
    assert sonuc.tahmini_talep == 0
    assert sonuc.gunluk_ortalama_talep == 0
    assert sonuc.onerilen_ikmal_miktari == 0
    assert sonuc.stok_riski == "yok"
    assert sonuc.talep_sinyali == "dusuk"
    assert sonuc.veri_guven_skoru == 0
    assert any("cold-start" in uyari for uyari in sonuc.uyarilar)


def test_yuksek_talep_ve_dusuk_stok_kritik_risk_uretmelidir() -> None:
    baslangic = date.today() - timedelta(days=29)
    features = InputFeatures(
        urun_id=3,
        stok_cikis_gecmisi=[
            DailyStockExit(tarih=baslangic + timedelta(days=index), miktar=20 + index)
            for index in range(30)
        ],
        mevcut_stok=50,
        min_stok=25,
    )
    sonuc = PredictDemandUseCase(BaselineMovingAveragePredictor()).execute(features)

    assert sonuc.tahmini_talep > features.mevcut_stok
    assert sonuc.onerilen_ikmal_miktari > 0
    assert sonuc.stok_riski == "kritik"
    assert sonuc.talep_sinyali == "yuksek"


def test_sentetik_veri_kaynagi_use_case_ile_calismali() -> None:
    data_source = SyntheticDemandDataSource(seed=123)
    profile = data_source.demo_profiles()[0]
    features = data_source.build_features(profile, days=90)
    sonuc = PredictDemandUseCase(BaselineMovingAveragePredictor()).execute(features)

    assert features.tenant_id == "demo-tenant"
    assert len(features.stok_cikis_gecmisi) == 90
    assert sonuc.urun_id == profile.urun_id
    assert sonuc.tahmini_talep > 0


def main() -> None:
    payload = baseline_tahmin_payload()
    print(payload)


if __name__ == "__main__":
    main()
