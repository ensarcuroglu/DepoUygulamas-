"""DI — RabbitMQ messaging factory'leri.

Settings'ten topoloji ve connection factory üretir; relay use case'i için
hazır bir publisher ve use case factory sağlar.

Scheduler job (`rabbitmq_outbox_relay_job`) DI'ı atlayıp doğrudan inşa
ediyor (lifecycle uyumsuzluğu için); FastAPI router içinde manuel relay
endpoint açılırsa buradan tüketilir.
"""

from __future__ import annotations

from fastapi import Depends

from app.application.use_cases.rabbitmq_outbox_relay_use_case import (
    RabbitMqOutboxRelayUseCase,
)
from app.core.config import Settings, get_settings
from app.infrastructure.di.modules.operator_performans_di import (
    get_gorev_performans_event_repo,
)
from app.infrastructure.messaging.connection import RabbitMqConnectionFactory
from app.infrastructure.messaging.publisher import RabbitMqPerformansPublisher
from app.infrastructure.messaging.topology import RabbitMqTopology


def get_rabbitmq_topology(
    settings: Settings = Depends(get_settings),
) -> RabbitMqTopology:
    return RabbitMqTopology(
        exchange=settings.rabbitmq_exchange,
        queue=settings.rabbitmq_queue,
        dlx=settings.rabbitmq_dlx,
    )


def get_rabbitmq_connection_factory(
    settings: Settings = Depends(get_settings),
) -> RabbitMqConnectionFactory:
    return RabbitMqConnectionFactory(url=settings.rabbitmq_url)


def get_rabbitmq_performans_publisher(
    factory: RabbitMqConnectionFactory = Depends(get_rabbitmq_connection_factory),
    topology: RabbitMqTopology = Depends(get_rabbitmq_topology),
) -> RabbitMqPerformansPublisher:
    return RabbitMqPerformansPublisher(factory, topology)


def get_rabbitmq_outbox_relay_uc(
    event_repo=Depends(get_gorev_performans_event_repo),
    publisher: RabbitMqPerformansPublisher = Depends(get_rabbitmq_performans_publisher),
    settings: Settings = Depends(get_settings),
) -> RabbitMqOutboxRelayUseCase:
    return RabbitMqOutboxRelayUseCase(
        event_repo=event_repo,
        publisher=publisher,
        batch_size=settings.rabbitmq_relay_batch_size,
    )
