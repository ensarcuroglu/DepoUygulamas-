from __future__ import annotations

from abc import ABC, abstractmethod

from ml_models.talep_tahmin.domain.entities import InputFeatures, PredictionResult


class ITimeSeriesPredictor(ABC):
    """Time-series predictor contract for demand forecasting."""

    @abstractmethod
    def predict(self, features: InputFeatures, tahmin_gun: int = 30) -> PredictionResult:
        """Return a demand prediction from prepared input features."""
        ...
