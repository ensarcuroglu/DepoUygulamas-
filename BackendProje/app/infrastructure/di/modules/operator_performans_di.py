"""DI — Operatör Performans (LMS) modülü.

Faz 1 kapsamı:
  - GorevPerformansEvent + OperatorVardiyaMetrikleri repo factory'leri
  - DbOutboxPerformansEventPublisher factory'si (IPerformansEventPublisher)
  - MetriklerAggregasyonUseCase factory'si (APScheduler tarafından çağrılır)

Hook'lar mevcut yerleştirme/toplama DI factory'lerine
`depo_envanter_di` ve `siparis_lojistik_di` modüllerinde inject edilir;
bu modül publisher'ı dışa açar, `Depends(get_performans_event_publisher)`
şeklinde kullanılır.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.core.services.operator_kpi_service import OperatorKpiService
from app.core.services.performans_event_publisher import IPerformansEventPublisher
from app.application.use_cases import MetriklerAggregasyonUseCase
from app.infrastructure.persistence.repositories import (
    SqlAlchemyGorevPerformansEventRepository,
    SqlAlchemyOperatorVardiyaMetrikleriRepository,
)
from app.infrastructure.services.db_outbox_performans_event_publisher import (
    DbOutboxPerformansEventPublisher,
)


# ── Repository factory'leri ──

def get_gorev_performans_event_repo(db: Session = Depends(get_db)):
    return SqlAlchemyGorevPerformansEventRepository(db)


def get_operator_vardiya_metrikleri_repo(db: Session = Depends(get_db)):
    return SqlAlchemyOperatorVardiyaMetrikleriRepository(db)


# ── Publisher factory ──

def get_performans_event_publisher(
    event_repo=Depends(get_gorev_performans_event_repo),
) -> IPerformansEventPublisher:
    """IPerformansEventPublisher — Faz 1 default: DB-tabanlı outbox.

    Faz 5'te aynı arayüzün RabbitMQ implementasyonu eklenebilir;
    use case kodu değişmez."""
    return DbOutboxPerformansEventPublisher(event_repo)


# ── Domain service ──

def get_operator_kpi_service() -> OperatorKpiService:
    return OperatorKpiService()


# ── Use case factory'leri ──

def get_metrikler_aggregasyon_uc(
    event_repo=Depends(get_gorev_performans_event_repo),
    metrik_repo=Depends(get_operator_vardiya_metrikleri_repo),
    kpi_service: OperatorKpiService = Depends(get_operator_kpi_service),
) -> MetriklerAggregasyonUseCase:
    return MetriklerAggregasyonUseCase(event_repo, metrik_repo, kpi_service)
