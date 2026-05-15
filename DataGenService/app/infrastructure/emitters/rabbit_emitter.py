"""RabbitMQ emitter — aio-pika persistent + publisher confirm + mandatory.

İki katmanlı tasarım:
  - `RabbitPublisher` Protocol     → ortak yayın arayüzü
  - `AioPikaPublisher`             → production implementasyonu
  - `RabbitEmitter` (IEmitter)     → DTO → JSON → publisher.publish

Bu ayrım, testte gerçek RabbitMQ olmadan in-memory publisher ile
emitter'ı doğrulamayı sağlar.

Routing:
  exchange = "depo.events" (topic, durable)
  routing key = "lms.gorev_performans.<event_tipi>" (DTO'dan üretilir)
  delivery_mode = 2 (persistent), mandatory = True, publisher confirm açık
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable, Sequence
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel

from .base import EmitSummary

if TYPE_CHECKING:
    import aio_pika

log = logging.getLogger("data-gen.rabbit")

RoutingKeyFn = Callable[[BaseModel], str]


class RabbitPublishError(RuntimeError):
    """Yayın başarısız (unroutable, network, vs.)."""


class RabbitPublisher(Protocol):
    """Soyut yayıncı — production aio-pika, test in-memory."""

    async def publish(
        self,
        *,
        routing_key: str,
        body: bytes,
        content_type: str = "application/json",
    ) -> None: ...

    async def close(self) -> None: ...


class RabbitEmitter:
    """`IEmitter` — Pydantic DTO listesini RabbitMQ exchange'ine yayar."""

    def __init__(
        self,
        *,
        publisher: RabbitPublisher,
        routing_key_fn: RoutingKeyFn,
        semaphore: asyncio.Semaphore,
    ) -> None:
        self.publisher = publisher
        self.routing_key_fn = routing_key_fn
        self.semaphore = semaphore

        self._summary = EmitSummary()
        self._closed = False

    # ------------------------------------------------------------------
    # IEmitter
    # ------------------------------------------------------------------

    async def emit_batch(self, items: Sequence[BaseModel]) -> None:
        if self._closed:
            raise RuntimeError("RabbitEmitter zaten kapalı.")
        if not items:
            return

        async def _one(item: BaseModel) -> None:
            async with self.semaphore:
                await self._publish_one(item)

        await asyncio.gather(*[_one(i) for i in items], return_exceptions=False)

    async def close(self) -> None:
        if self._closed:
            return
        await self.publisher.close()
        self._summary.mark_finished()
        self._closed = True

    def summary(self) -> EmitSummary:
        return self._summary

    async def __aenter__(self) -> RabbitEmitter:
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _publish_one(self, item: BaseModel) -> None:
        t0 = time.perf_counter()
        try:
            routing_key = self.routing_key_fn(item)
            body = item.model_dump_json().encode("utf-8")
            await self.publisher.publish(
                routing_key=routing_key,
                body=body,
                content_type="application/json",
            )
        except Exception as exc:
            self._summary.total += 1
            self._summary.failed += 1
            self._summary.errors.append(f"{type(exc).__name__}: {exc}")
            self._summary.latencies_ms.append(
                (time.perf_counter() - t0) * 1000.0
            )
            log.warning("Rabbit emit fail: %s", exc)
        else:
            self._summary.total += 1
            self._summary.success += 1
            self._summary.latencies_ms.append(
                (time.perf_counter() - t0) * 1000.0
            )


class InMemoryRabbitPublisher:
    """Test ve dry-run için in-memory publisher.

    Yayınlanan mesajlar `published` listesine eklenir; gerçek ağ yok.
    """

    def __init__(
        self,
        *,
        on_publish: Callable[[str, bytes], Awaitable[None] | None] | None = None,
        fail_routing_keys: set[str] | None = None,
    ) -> None:
        self.published: list[tuple[str, bytes]] = []
        self.on_publish = on_publish
        self.fail_routing_keys = fail_routing_keys or set()
        self.closed = False

    async def publish(
        self,
        *,
        routing_key: str,
        body: bytes,
        content_type: str = "application/json",
    ) -> None:
        if routing_key in self.fail_routing_keys:
            raise RabbitPublishError(f"unroutable: {routing_key}")
        self.published.append((routing_key, body))
        if self.on_publish is not None:
            result = self.on_publish(routing_key, body)
            if asyncio.iscoroutine(result):
                await result

    async def close(self) -> None:
        self.closed = True


class AioPikaPublisher:
    """`RabbitPublisher` production implementasyonu (aio-pika).

    Topology declare BackendProje'deki publisher'la birebir uyumlu:
      exchange = topic, durable
      delivery_mode = PERSISTENT
      mandatory = True
      publisher confirms = True (RobustConnection default)
    """

    def __init__(
        self,
        *,
        connection: "aio_pika.abc.AbstractRobustConnection",
        exchange: "aio_pika.abc.AbstractExchange",
    ) -> None:
        self._connection = connection
        self._exchange = exchange

    @classmethod
    async def connect(
        cls,
        *,
        url: str,
        exchange_name: str = "depo.events",
    ) -> AioPikaPublisher:
        import aio_pika
        from aio_pika import DeliveryMode, ExchangeType  # noqa: F401

        connection = await aio_pika.connect_robust(url)
        channel = await connection.channel(publisher_confirms=True)
        exchange = await channel.declare_exchange(
            exchange_name, ExchangeType.TOPIC, durable=True
        )
        return cls(connection=connection, exchange=exchange)

    async def publish(
        self,
        *,
        routing_key: str,
        body: bytes,
        content_type: str = "application/json",
    ) -> None:
        import aio_pika

        message = aio_pika.Message(
            body=body,
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type=content_type,
        )
        try:
            await self._exchange.publish(
                message, routing_key=routing_key, mandatory=True
            )
        except aio_pika.exceptions.DeliveryError as exc:
            raise RabbitPublishError(
                f"DeliveryError (unroutable veya nack) routing_key={routing_key}: {exc}"
            ) from exc

    async def close(self) -> None:
        await self._connection.close()


def lms_routing_key_for(event_tipi_attr: str = "event_tipi") -> RoutingKeyFn:
    """`lms.gorev_performans.<event_tipi>` routing key üretici factory."""

    def _fn(item: BaseModel) -> str:
        event_tipi = getattr(item, event_tipi_attr, None)
        if not event_tipi:
            raise ValueError(
                f"DTO'da `{event_tipi_attr}` alanı yok; routing key üretilemiyor."
            )
        return f"lms.gorev_performans.{event_tipi}"

    return _fn
