"""Operatör Performans (LMS) — Metrik Aggregator Job.

APScheduler ile periyodik olarak (varsayılan her 5 dakika)
`gorev_performans_eventleri` tablosundaki `aggregate_edildi=False` kayıtları
okur, OperatorKpiService ile vardiya kovalarına böler ve
`operator_vardiya_metrikleri` tablosuna upsert eder.

DI lifecycle'ı scheduler context'inden bağımsız tutmak için repository ve
use case nesneleri elle oluşturulur (talep_tahmin_job pattern'i).
"""

from __future__ import annotations

import logging

from database import SessionLocal
from app.application.use_cases.operator_performans_use_cases import (
    MetriklerAggregasyonUseCase,
)
from app.core.services.operator_kpi_service import OperatorKpiService
from app.infrastructure.persistence.repositories import (
    SqlAlchemyGorevPerformansEventRepository,
    SqlAlchemyOperatorVardiyaMetrikleriRepository,
)

logger = logging.getLogger(__name__)


def operator_metrikleri_aggregate_et() -> None:
    """Bekleyen performans event'lerini vardiya metriklerine aggregate eder."""
    db = SessionLocal()
    try:
        event_repo = SqlAlchemyGorevPerformansEventRepository(db)
        metrik_repo = SqlAlchemyOperatorVardiyaMetrikleriRepository(db)
        kpi_service = OperatorKpiService()

        uc = MetriklerAggregasyonUseCase(event_repo, metrik_repo, kpi_service)
        sonuc = uc.execute()

        if sonuc.islenen_event > 0:
            logger.info(
                "Operatör metrik aggregasyon: islenen=%d, vardiya=%d, kalan~%d",
                sonuc.islenen_event,
                sonuc.guncellenen_vardiya,
                sonuc.bekleyen_kalan,
            )
    except Exception as exc:
        logger.error("Operatör metrik aggregasyon hatası: %s", exc)
        db.rollback()
    finally:
        db.close()
