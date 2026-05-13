"""RabbitMQ publisher — publisher confirm açık, persistent mesaj.

Tek mesaj ya da batch publish için kullanılır. Her publish başlangıcında
topology idempotent declare edilir; bu connection paylaşılırken bile
güvenli — RabbitMQ aynı parametrelerle yeniden declare'i no-op kabul eder.

Bağlantı yaşam döngüsü çağıran tarafa bırakılmıştır: relay job
`open() / publish()*N / close()` çağırır.
"""

from __future__ import annotations

import logging
from typing import Optional

import pika
from pika.exceptions import (
    AMQPConnectionError,
    AMQPError,
    UnroutableError,
)

from app.core.entities.operator_performans import GorevPerformansEvent
from app.infrastructure.messaging.connection import (
    RabbitMqConnectionFactory,
    RabbitMqUnavailable,
)
from app.infrastructure.messaging.serializer import serialize_performans_event
from app.infrastructure.messaging.topology import RabbitMqTopology


logger = logging.getLogger(__name__)


class RabbitMqPerformansPublisher:
    """LMS performans event yayınlayıcısı.

    Kullanım:
        publisher = RabbitMqPerformansPublisher(factory, topology)
        publisher.open()
        try:
            for event in events:
                publisher.publish(event)
        finally:
            publisher.close()
    """

    def __init__(
        self,
        connection_factory: RabbitMqConnectionFactory,
        topology: RabbitMqTopology,
    ) -> None:
        self._factory = connection_factory
        self._topology = topology
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None

    def open(self) -> None:
        """Bağlantı + kanal açar, topoloji declare eder, confirm modunu açar."""
        if self._channel is not None:
            return
        self._connection = self._factory.connect()
        self._channel = self._connection.channel()
        self._topology.declare(self._channel)
        self._channel.confirm_delivery()

    def publish(self, event: GorevPerformansEvent) -> None:
        """Event'i exchange'e persistent + mandatory olarak yayınlar.

        Broker confirm vermezse pika `NackError` veya `UnroutableError` fırlatır;
        bunlar çağırana yansıtılır (relay deneme sayısını arttırır).
        """
        if self._channel is None:
            raise RuntimeError("publish() çağrısından önce open() çağrılmalı")

        body = serialize_performans_event(event)
        properties = pika.BasicProperties(
            content_type="application/json",
            content_encoding="utf-8",
            delivery_mode=2,  # persistent
            message_id=event.event_uuid,
            type=event.event_tipi,
        )
        routing_key = self._topology.routing_key_for_event(event.event_tipi)
        try:
            self._channel.basic_publish(
                exchange=self._topology.exchange,
                routing_key=routing_key,
                body=body,
                properties=properties,
                mandatory=True,
            )
        except UnroutableError as exc:
            raise RuntimeError(
                f"Event {event.event_uuid} routing_key={routing_key} unroutable"
            ) from exc
        except AMQPConnectionError as exc:
            raise RabbitMqUnavailable(
                f"Publish sırasında bağlantı koptu: {exc}"
            ) from exc
        except AMQPError:
            # Diğer AMQP hatalarını ham hâliyle yukarı taşı.
            raise

    def close(self) -> None:
        try:
            if self._channel is not None and self._channel.is_open:
                self._channel.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("RabbitMQ kanal kapatma uyarısı: %s", exc)
        finally:
            self._channel = None
            self._factory.safe_close(self._connection)
            self._connection = None
