"""DI - Talep Tahmini.

Algoritma `ml_models.talep_tahmin` paketinden gelir; bu modul predictor
ve use case factory'lerini FastAPI Depends() zincirine baglar.
"""

from pathlib import Path

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.application.use_cases import (
    BacktestOzetGetirUseCase,
    ParquetBacktestUseCase,
    RiskliUrunlerListeleUseCase,
    TalepTahminUrunleriListeleUseCase,
    TalepTahminiGetirUseCase,
)
from app.infrastructure.persistence.repositories import (
    SqlAlchemyTalepTahminCacheRepository,
    SqlAlchemyTalepTahminiRepository,
)
import logging

from ml_models.talep_tahmin.application import PredictDemandUseCase
from ml_models.talep_tahmin.domain import ITimeSeriesPredictor
from ml_models.talep_tahmin.infrastructure import (
    BaselineMovingAveragePredictor,
    SklearnGradientBoostingPredictor,
)

_logger = logging.getLogger(__name__)
_PREDICTOR_SINGLETON: ITimeSeriesPredictor | None = None


def get_talep_tahmin_predictor() -> ITimeSeriesPredictor:
    """Process-omru boyunca tek bir predictor instance kullan.

    Sklearn kuruluysa SklearnGradientBoostingPredictor; aksi halde
    baseline'a fallback. Sklearn predictor zaten icinde veri yetersiz
    olunca baseline'a dusuyor — bu factory sadece kurulum eksikligine
    bakiyor.
    """
    global _PREDICTOR_SINGLETON
    if _PREDICTOR_SINGLETON is not None:
        return _PREDICTOR_SINGLETON

    try:
        import sklearn  # noqa: F401

        _PREDICTOR_SINGLETON = SklearnGradientBoostingPredictor()
        _logger.info("Talep tahmini: SklearnGradientBoostingPredictor aktif.")
    except ImportError:
        _PREDICTOR_SINGLETON = BaselineMovingAveragePredictor()
        _logger.warning(
            "Talep tahmini: sklearn yok, BaselineMovingAveragePredictor kullaniliyor."
        )
    return _PREDICTOR_SINGLETON


def get_talep_tahmin_predict_uc(
    predictor: ITimeSeriesPredictor = Depends(get_talep_tahmin_predictor),
) -> PredictDemandUseCase:
    return PredictDemandUseCase(predictor)


def get_talep_tahmini_repo(db: Session = Depends(get_db)):
    return SqlAlchemyTalepTahminiRepository(db)


def get_talep_tahmin_cache_repo(db: Session = Depends(get_db)):
    return SqlAlchemyTalepTahminCacheRepository(db)


def get_talep_tahmin_urunleri_listele_uc(
    repo=Depends(get_talep_tahmini_repo),
):
    return TalepTahminUrunleriListeleUseCase(repo)


def get_talep_tahmini_getir_uc(
    repo=Depends(get_talep_tahmini_repo),
    predict_uc: PredictDemandUseCase = Depends(get_talep_tahmin_predict_uc),
    cache_repo=Depends(get_talep_tahmin_cache_repo),
):
    return TalepTahminiGetirUseCase(repo, predict_uc, cache_repo=cache_repo)


def get_riskli_urunler_listele_uc(
    repo=Depends(get_talep_tahmini_repo),
    cache_repo=Depends(get_talep_tahmin_cache_repo),
):
    return RiskliUrunlerListeleUseCase(repo, cache_repo)


def get_backtest_ozet_getir_uc(
    repo=Depends(get_talep_tahmini_repo),
    predict_uc: PredictDemandUseCase = Depends(get_talep_tahmin_predict_uc),
):
    return BacktestOzetGetirUseCase(repo, predict_uc)


# ml_models/talep_tahmin/data/raw — proje kokunden relative
# parents: [0]=modules [1]=di [2]=infrastructure [3]=app [4]=BackendProje [5]=root
_PARQUET_DIR = (
    Path(__file__).resolve().parents[5]
    / "ml_models"
    / "talep_tahmin"
    / "data"
    / "raw"
)


def get_talep_tahmin_parquet_dir() -> Path:
    return _PARQUET_DIR


def get_parquet_backtest_uc(
    predict_uc: PredictDemandUseCase = Depends(get_talep_tahmin_predict_uc),
    parquet_dir: Path = Depends(get_talep_tahmin_parquet_dir),
) -> ParquetBacktestUseCase:
    return ParquetBacktestUseCase(predict_uc=predict_uc, parquet_dir=parquet_dir)
