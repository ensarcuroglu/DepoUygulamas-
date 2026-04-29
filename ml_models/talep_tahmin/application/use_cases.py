from __future__ import annotations

from typing import Any, Mapping

from ml_models.talep_tahmin.domain.entities import InputFeatures, PredictionResult
from ml_models.talep_tahmin.domain.predictor import ITimeSeriesPredictor


class PredictDemandUseCase:
    """Prepare input features and execute the configured demand predictor."""

    def __init__(self, predictor: ITimeSeriesPredictor) -> None:
        self._predictor = predictor

    def execute(
        self,
        features: InputFeatures | Mapping[str, Any],
        tahmin_gun: int = 30,
    ) -> PredictionResult:
        prepared_features = self._features_hazirla(features)
        return self._predictor.predict(features=prepared_features, tahmin_gun=tahmin_gun)

    @staticmethod
    def _features_hazirla(features: InputFeatures | Mapping[str, Any]) -> InputFeatures:
        if isinstance(features, InputFeatures):
            return features
        return InputFeatures.model_validate(features)
