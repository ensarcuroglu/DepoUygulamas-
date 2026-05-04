"""Sklearn GradientBoosting predictor unit tests.

Bu modul sklearn olmadiginda otomatik atlanir (pytest.importorskip).
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest

pytest.importorskip("sklearn")
pytest.importorskip("numpy")

from ml_models.talep_tahmin.domain import DailyStockExit, InputFeatures  # noqa: E402
from ml_models.talep_tahmin.infrastructure import SklearnGradientBoostingPredictor  # noqa: E402

pytestmark = pytest.mark.unit


def _stabil_seri(gun: int = 90, miktar: float = 8.0) -> list[DailyStockExit]:
    baslangic = date.today() - timedelta(days=gun - 1)
    return [
        DailyStockExit(tarih=baslangic + timedelta(days=i), miktar=miktar + (i % 3))
        for i in range(gun)
    ]


def test_sklearn_predictor_temel_tahmin_uretir():
    predictor = SklearnGradientBoostingPredictor()
    features = InputFeatures(
        urun_id=1,
        stok_cikis_gecmisi=_stabil_seri(),
        mevcut_stok=200,
        min_stok=30,
    )

    sonuc = predictor.predict(features=features, tahmin_gun=7)

    assert sonuc.urun_id == 1
    assert sonuc.tahmin_gun == 7
    assert sonuc.tahmini_talep > 0
    assert len(sonuc.gunluk_tahmin_serisi) == 7
    for nokta in sonuc.gunluk_tahmin_serisi:
        assert nokta.alt_sinir <= nokta.tahmin <= nokta.ust_sinir
    assert sonuc.model_versiyonu


def test_sklearn_predictor_az_veri_baseline_fallback():
    predictor = SklearnGradientBoostingPredictor()
    features = InputFeatures(
        urun_id=2,
        stok_cikis_gecmisi=_stabil_seri(gun=10),
        mevcut_stok=100,
        min_stok=20,
    )

    sonuc = predictor.predict(features=features, tahmin_gun=7)

    assert sonuc.urun_id == 2
    assert "fallback" in sonuc.model_versiyonu or "baseline" in sonuc.model_versiyonu


def test_sklearn_predictor_cold_start():
    predictor = SklearnGradientBoostingPredictor()
    features = InputFeatures(
        urun_id=3,
        stok_cikis_gecmisi=[],
        mevcut_stok=100,
        min_stok=20,
    )

    sonuc = predictor.predict(features=features, tahmin_gun=7)

    assert sonuc.tahmini_talep == 0
    assert sonuc.veri_guven_skoru == 0
