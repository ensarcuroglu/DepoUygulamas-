from __future__ import annotations

from pathlib import Path
import json
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_models.talep_tahmin.application import PredictDemandUseCase
from ml_models.talep_tahmin.domain import InputFeatures
from ml_models.talep_tahmin.infrastructure import BaselineMovingAveragePredictor
from ml_models.talep_tahmin.infrastructure.data_sources import SyntheticDemandDataSource

try:
    from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
except ModuleNotFoundError:
    def mean_absolute_error(actual_values: list[float], predicted_values: list[float]) -> float:
        return sum(
            abs(actual - predicted)
            for actual, predicted in zip(actual_values, predicted_values)
        ) / len(actual_values)

    def mean_absolute_percentage_error(
        actual_values: list[float],
        predicted_values: list[float],
    ) -> float:
        errors = []
        for actual, predicted in zip(actual_values, predicted_values):
            if actual == 0:
                continue
            errors.append(abs((actual - predicted) / actual))
        return sum(errors) / len(errors) if errors else 0.0


def run_backtest(tahmin_gun: int = 30) -> dict:
    data_source = SyntheticDemandDataSource(seed=2026)
    use_case = PredictDemandUseCase(BaselineMovingAveragePredictor())

    actual_values: list[float] = []
    predicted_values: list[float] = []
    urun_sonuclari: list[dict] = []

    for profile in data_source.demo_profiles():
        full_features = data_source.build_features(profile, days=90)
        train_series = full_features.stok_cikis_gecmisi[:-tahmin_gun]
        test_series = full_features.stok_cikis_gecmisi[-tahmin_gun:]
        actual = round(sum(item.miktar for item in test_series), 2)

        train_features = InputFeatures(
            urun_id=full_features.urun_id,
            tenant_id=full_features.tenant_id,
            stok_cikis_gecmisi=train_series,
            mevcut_stok=full_features.mevcut_stok,
            min_stok=full_features.min_stok,
        )
        prediction = use_case.execute(train_features, tahmin_gun=tahmin_gun)

        actual_values.append(actual)
        predicted_values.append(prediction.tahmini_talep)
        urun_sonuclari.append(
            {
                "urun_id": profile.urun_id,
                "gercek_talep": actual,
                "tahmini_talep": prediction.tahmini_talep,
                "mutlak_hata": round(abs(actual - prediction.tahmini_talep), 2),
                "stok_riski": prediction.stok_riski,
                "veri_guven_skoru": prediction.veri_guven_skoru,
            }
        )

    return {
        "tahmin_gun": tahmin_gun,
        "mae": round(mean_absolute_error(actual_values, predicted_values), 2),
        "mape": round(mean_absolute_percentage_error(actual_values, predicted_values), 4),
        "urunler": urun_sonuclari,
    }


def main() -> None:
    print(json.dumps(run_backtest(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
