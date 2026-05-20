"""DataGenService `timeseries_history` parquet ciktisi uzerinde baseline backtest.

Bu deneysel betik, `ml_models/talep_tahmin/data/raw/` altindaki DataGenService
parquet dosyasini okur, kanonik `InputFeatures` formatina cevirir ve
`BaselineMovingAveragePredictor` icin per-urun MAE/MAPE raporu basar.

Deneysel kod statusunde tutulur; uretim adaptoru icin `ParquetDemandDataSource`
infrastructure katmanina eklenecek.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml_models.talep_tahmin.application import PredictDemandUseCase
from ml_models.talep_tahmin.domain import InputFeatures
from ml_models.talep_tahmin.infrastructure import BaselineMovingAveragePredictor
from ml_models.talep_tahmin.infrastructure.data_sources import ParquetDemandDataSource

DEFAULT_PARQUET = (
    PROJECT_ROOT
    / "ml_models"
    / "talep_tahmin"
    / "data"
    / "raw"
    / "talep_gecmis_20240101_seed42_u10_g30.parquet"
)


def _mae(actual: list[float], predicted: list[float]) -> float:
    if not actual:
        return 0.0
    return sum(abs(a - p) for a, p in zip(actual, predicted)) / len(actual)


def _mape(actual: list[float], predicted: list[float]) -> float:
    errors = [abs((a - p) / a) for a, p in zip(actual, predicted) if a]
    return sum(errors) / len(errors) if errors else 0.0


def run(parquet_path: Path, tahmin_gun: int) -> dict:
    data_source = ParquetDemandDataSource(parquet_path, max_gun=730)
    use_case = PredictDemandUseCase(BaselineMovingAveragePredictor())

    urun_sonuclari: list[dict] = []
    actual_values: list[float] = []
    predicted_values: list[float] = []

    for urun_id in data_source.available_urun_ids():
        full_features = data_source.build_features(urun_id)
        seri = full_features.stok_cikis_gecmisi
        if len(seri) <= tahmin_gun:
            continue

        train_series = seri[:-tahmin_gun]
        test_series = seri[-tahmin_gun:]
        gercek_talep = round(sum(item.miktar for item in test_series), 2)

        features = InputFeatures(
            urun_id=full_features.urun_id,
            tenant_id=full_features.tenant_id,
            stok_cikis_gecmisi=train_series,
            mevcut_stok=full_features.mevcut_stok,
            min_stok=full_features.min_stok,
        )
        prediction = use_case.execute(features, tahmin_gun=tahmin_gun)

        actual_values.append(gercek_talep)
        predicted_values.append(prediction.tahmini_talep)
        urun_sonuclari.append(
            {
                "urun_id": int(urun_id),
                "gercek_talep": gercek_talep,
                "tahmini_talep": prediction.tahmini_talep,
                "mutlak_hata": round(abs(gercek_talep - prediction.tahmini_talep), 2),
                "veri_guven_skoru": prediction.veri_guven_skoru,
                "talep_sinyali": prediction.talep_sinyali,
            }
        )

    return {
        "parquet": str(parquet_path),
        "tahmin_gun": tahmin_gun,
        "urun_sayisi": len(urun_sonuclari),
        "mae": round(_mae(actual_values, predicted_values), 2),
        "mape": round(_mape(actual_values, predicted_values), 4),
        "urunler": urun_sonuclari,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--parquet",
        type=Path,
        default=DEFAULT_PARQUET,
        help="DataGenService parquet ciktisi yolu.",
    )
    parser.add_argument(
        "--tahmin-gun",
        type=int,
        default=7,
        help="Backtest icin holdout uzunlugu (gun).",
    )
    args = parser.parse_args()

    sonuc = run(args.parquet, args.tahmin_gun)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
