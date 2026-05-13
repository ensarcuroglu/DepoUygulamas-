"""RabbitMQ messaging altyapısı (LMS Operatör Performans event hattı).

Faz 3 kapsamı:
  connection  — pika BlockingConnection factory (lazy)
  topology    — exchange/queue/DLX idempotent declare
  serializer  — GorevPerformansEvent ↔ JSON (schema_version=1)
  publisher   — publisher confirm açık, persistent mesaj

Faz 4'te bu paket içine `operator_performans_consumer.py` eklenecek.
"""

from app.infrastructure.messaging.connection import (
    RabbitMqConnectionFactory,
    RabbitMqUnavailable,
)
from app.infrastructure.messaging.publisher import RabbitMqPerformansPublisher
from app.infrastructure.messaging.serializer import (
    PERFORMANS_EVENT_SCHEMA_VERSION,
    deserialize_performans_event,
    serialize_performans_event,
)
from app.infrastructure.messaging.topology import RabbitMqTopology

__all__ = [
    "RabbitMqConnectionFactory",
    "RabbitMqUnavailable",
    "RabbitMqPerformansPublisher",
    "RabbitMqTopology",
    "PERFORMANS_EVENT_SCHEMA_VERSION",
    "serialize_performans_event",
    "deserialize_performans_event",
]
