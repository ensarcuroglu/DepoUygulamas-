"""Faz 5 — RabbitEmitter testleri (in-memory publisher)."""

from __future__ import annotations

import asyncio
import json

import pytest

from app.factories import PerformansEventFactory
from app.infrastructure.emitters import (
    InMemoryRabbitPublisher,
    RabbitEmitter,
    lms_routing_key_for,
)


@pytest.mark.unit
async def test_routing_key_for_each_event_tipi() -> None:
    publisher = InMemoryRabbitPublisher()
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for("event_tipi"),
        semaphore=asyncio.Semaphore(4),
    )
    events = PerformansEventFactory(seed=42).build_many(50)
    await emitter.emit_batch(events)
    await emitter.close()

    assert emitter.summary().success == 50
    assert emitter.summary().failed == 0

    # Her mesajın routing key'i lms.gorev_performans.<event_tipi>
    routing_keys = [rk for rk, _ in publisher.published]
    assert all(rk.startswith("lms.gorev_performans.") for rk in routing_keys)

    # Routing key suffix'i mesajın event_tipi alanıyla eşleşmeli
    for (rk, body), event in zip(publisher.published, events):
        payload = json.loads(body)
        assert rk == f"lms.gorev_performans.{payload['event_tipi']}"
        assert payload["event_uuid"] == event.event_uuid


@pytest.mark.unit
async def test_body_is_valid_utf8_json() -> None:
    publisher = InMemoryRabbitPublisher()
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for(),
        semaphore=asyncio.Semaphore(2),
    )
    events = PerformansEventFactory(seed=1).build_many(5)
    await emitter.emit_batch(events)
    await emitter.close()

    for _, body in publisher.published:
        parsed = json.loads(body.decode("utf-8"))
        assert "event_uuid" in parsed
        assert "olusturma_tarihi" in parsed


@pytest.mark.unit
async def test_unroutable_message_counted_as_failed() -> None:
    """fail_routing_keys ile bir event tipi 'unroutable' simüle edilir."""
    publisher = InMemoryRabbitPublisher(
        fail_routing_keys={"lms.gorev_performans.GOREV_IPTAL"}
    )
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for(),
        semaphore=asyncio.Semaphore(4),
    )
    events = PerformansEventFactory(seed=42).build_many(200)
    await emitter.emit_batch(events)
    await emitter.close()

    summary = emitter.summary()
    expected_failed = sum(1 for e in events if e.event_tipi == "GOREV_IPTAL")
    assert summary.failed == expected_failed
    assert summary.success == 200 - expected_failed
    # Hata mesajları kaydedildi
    assert summary.errors and "unroutable" in summary.errors[0]


@pytest.mark.unit
async def test_close_is_idempotent() -> None:
    publisher = InMemoryRabbitPublisher()
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for(),
        semaphore=asyncio.Semaphore(1),
    )
    await emitter.close()
    await emitter.close()  # ikinci çağrı no-op olmalı
    assert publisher.closed is True


@pytest.mark.unit
async def test_cannot_emit_after_close() -> None:
    publisher = InMemoryRabbitPublisher()
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for(),
        semaphore=asyncio.Semaphore(1),
    )
    await emitter.close()
    with pytest.raises(RuntimeError, match="zaten kapalı"):
        await emitter.emit_batch(
            PerformansEventFactory(seed=1).build_many(1)
        )


@pytest.mark.unit
async def test_empty_batch_noop() -> None:
    publisher = InMemoryRabbitPublisher()
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for(),
        semaphore=asyncio.Semaphore(1),
    )
    await emitter.emit_batch([])
    assert emitter.summary().total == 0
    assert publisher.published == []


@pytest.mark.unit
async def test_concurrency_limit_respected() -> None:
    inflight = {"current": 0, "max_seen": 0}

    async def on_pub(rk: str, body: bytes) -> None:
        inflight["current"] += 1
        inflight["max_seen"] = max(inflight["max_seen"], inflight["current"])
        await asyncio.sleep(0.02)
        inflight["current"] -= 1

    publisher = InMemoryRabbitPublisher(on_publish=on_pub)
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for(),
        semaphore=asyncio.Semaphore(3),
    )
    await emitter.emit_batch(PerformansEventFactory(seed=42).build_many(15))
    assert inflight["max_seen"] <= 3


@pytest.mark.unit
def test_routing_key_factory_missing_attr() -> None:
    from pydantic import BaseModel

    class Bos(BaseModel):
        sayi: int

    fn = lms_routing_key_for("event_tipi")
    with pytest.raises(ValueError, match="event_tipi"):
        fn(Bos(sayi=1))
