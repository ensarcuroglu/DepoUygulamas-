"""RabbitMQ Outbox Relay Job (APScheduler).

`RABBITMQ_ENABLED=true` iken her 10 saniyede bir `gorev_performans_eventleri`
tablosundan yayınlanmamış event'leri RabbitMQ'ya pompalar.

DI lifecycle'ı APScheduler context'inden bağımsız tutmak için repository,
connection factory ve publisher elle kurulur (`operator_metrik_aggregator_job`
pattern'i).
"""

from __future__ import annotations

import logging

from app.application.use_cases.rabbitmq_outbox_relay_use_case import (
    RabbitMqOutboxRelayUseCase,
)
from app.core.config import get_settings
from app.infrastructure.messaging.connection import RabbitMqConnectionFactory
from app.infrastructure.messaging.publisher import RabbitMqPerformansPublisher
from app.infrastructure.messaging.topology import RabbitMqTopology
from app.infrastructure.persistence.repositories import (
    SqlAlchemyGorevPerformansEventRepository,
)
from database import SessionLocal

logger = logging.getLogger(__name__)


def rabbitmq_outbox_relay() -> None:
    """Outbox'tan bekleyen event'leri RabbitMQ'ya publish eder."""
    settings = get_settings()
    if not settings.rabbitmq_enabled:
        return

    db = SessionLocal()
    try:
        event_repo = SqlAlchemyGorevPerformansEventRepository(db)
        topology = RabbitMqTopology(
            exchange=settings.rabbitmq_exchange,
            queue=settings.rabbitmq_queue,
            dlx=settings.rabbitmq_dlx,
        )
        factory = RabbitMqConnectionFactory(url=settings.rabbitmq_url)
        publisher = RabbitMqPerformansPublisher(factory, topology)

        uc = RabbitMqOutboxRelayUseCase(
            event_repo=event_repo,
            publisher=publisher,
            batch_size=settings.rabbitmq_relay_batch_size,
        )
        sonuc = uc.execute()

        if sonuc.broker_kapali:
            logger.warning(
                "RabbitMQ relay: broker kapalı, sonraki çağrıda tekrar denenecek "
                "(okunan=%d, yayinlanan=%d)",
                sonuc.okunan,
                sonuc.yayinlanan,
            )
        elif sonuc.yayinlanan or sonuc.hatali:
            logger.info(
                "RabbitMQ relay: okunan=%d yayinlanan=%d hatali=%d",
                sonuc.okunan,
                sonuc.yayinlanan,
                sonuc.hatali,
            )
    except Exception as exc:  # noqa: BLE001
        logger.error("RabbitMQ outbox relay beklenmeyen hata: %s", exc)
        db.rollback()
    finally:
        db.close()
