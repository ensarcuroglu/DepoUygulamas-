"""`task_load` senaryosu — LMS event hattı / toplama görev yayın yükü.

İki mod (envanter §2):
  - target='rabbit'  → `PerformansEventFactory` → `RabbitEmitter`.
                       Saf yük testi: queue throughput + DLQ davranışı.
                       Consumer DB'de event_id bulamadığı için DLQ'ya
                       düşmesi BEKLENEN davranıştır.
  - target='rest'    → `ToplamaGoreviDTO` → `RestEmitter` →
                       `POST /api/v1/toplama-gorevleri/uret`. Use case
                       doğal outbox akışı tetiklenir; anlamlı LMS yükü.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import httpx

from app.core.config import Settings
from app.factories import (
    PerformansEventFactory,
    ReferenceTable,
    ToplamaGorevFactory,
)
from app.infrastructure.auth import JwtAuthClient
from app.infrastructure.emitters import (
    AioPikaPublisher,
    InMemoryRabbitPublisher,
    RabbitEmitter,
    RabbitPublisher,
    RestEmitter,
    lms_routing_key_for,
)

from .target_matrix import validate_target
from .timeseries_history import ScenarioResult

log = logging.getLogger("data-gen.scenario.task_load")

TaskLoadTarget = Literal["rest", "rabbit"]


@dataclass(frozen=True)
class TaskLoadParams:
    """`task_load` parametreleri."""

    count: int = 200
    seed: int = 42
    target: TaskLoadTarget = "rest"
    batch_size: int = 100
    concurrency: int = 10
    # rabbit modu için
    kullanici_count: int = 50
    depo_count: int = 3
    # rest modu için (sevkiyat_id pool boş → fallback index)
    sevkiyat_pool: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        validate_target("task_load", self.target)
        if self.count < 1:
            raise ValueError("count >= 1 olmalı")
        if self.batch_size < 1:
            raise ValueError("batch_size >= 1 olmalı")
        if self.concurrency < 1:
            raise ValueError("concurrency >= 1 olmalı")


def _chunks(items: Sequence, size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]


# ---------------------------------------------------------------------------
# Rabbit modu
# ---------------------------------------------------------------------------


async def _run_rabbit(
    params: TaskLoadParams,
    settings: Settings,
    publisher: RabbitPublisher | None = None,
) -> ScenarioResult:
    own_publisher = publisher is None
    if publisher is None:
        publisher = await AioPikaPublisher.connect(
            url=settings.rabbitmq_url,
            exchange_name=settings.rabbitmq_exchange,
        )

    factory = PerformansEventFactory(
        seed=params.seed,
        kullanici_count=params.kullanici_count,
        depo_count=params.depo_count,
    )
    events = factory.build_many(params.count)

    semaphore = asyncio.Semaphore(params.concurrency)
    emitter = RabbitEmitter(
        publisher=publisher,
        routing_key_fn=lms_routing_key_for("event_tipi"),
        semaphore=semaphore,
    )
    try:
        for batch in _chunks(events, params.batch_size):
            await emitter.emit_batch(batch)
    finally:
        if own_publisher:
            await emitter.close()
        else:
            # Publisher dışarıdan geldi; emitter'ı state'i ile kapatıp
            # publisher'ı caller'a bırak.
            emitter._summary.mark_finished()  # noqa: SLF001
            emitter._closed = True  # noqa: SLF001

    summary = emitter.summary()
    log.info(
        "task_load[rabbit]: total=%d success=%d failed=%d",
        summary.total,
        summary.success,
        summary.failed,
    )
    return ScenarioResult(
        scenario="task_load",
        output_path=None,
        total=summary.total,
        success=summary.success,
        failed=summary.failed,
        duration_sec=summary.duration_sec,
        p95_latency_ms=summary.p95_latency_ms,
        errors=summary.errors,
    )


# ---------------------------------------------------------------------------
# Rest modu
# ---------------------------------------------------------------------------


async def _run_rest(
    params: TaskLoadParams,
    settings: Settings,
    client: httpx.AsyncClient | None = None,
) -> ScenarioResult:
    own_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            base_url=settings.backend_base_url,
            timeout=httpx.Timeout(settings.http_timeout_sec),
        )

    try:
        auth = JwtAuthClient(
            base_url=settings.backend_base_url,
            username=settings.datagen_admin_username or "",
            password=settings.datagen_admin_password or "",
            client=client,
            refresh_buffer_sec=settings.jwt_refresh_buffer_sec,
        )
        semaphore = asyncio.Semaphore(params.concurrency)

        sevkiyat_pool = ReferenceTable()
        for sid in params.sevkiyat_pool:
            sevkiyat_pool.add({"id": sid})

        dtos = ToplamaGorevFactory(
            seed=params.seed, sevkiyat_pool=sevkiyat_pool
        ).build_many(params.count)

        emitter = RestEmitter(
            client=client,
            path="/api/v1/toplama-gorevleri/uret",
            auth=auth,
            semaphore=semaphore,
            idempotency=True,  # backend envanter §1.4'e göre destekli
        )
        for batch in _chunks(dtos, params.batch_size):
            await emitter.emit_batch(batch)

        summary = emitter.summary()
        log.info(
            "task_load[rest]: total=%d success=%d failed=%d",
            summary.total,
            summary.success,
            summary.failed,
        )
        return ScenarioResult(
            scenario="task_load",
            output_path=None,
            total=summary.total,
            success=summary.success,
            failed=summary.failed,
            duration_sec=summary.duration_sec,
            p95_latency_ms=summary.p95_latency_ms,
            errors=summary.errors,
        )
    finally:
        if own_client:
            await client.aclose()


# ---------------------------------------------------------------------------
# Public entry
# ---------------------------------------------------------------------------


async def run_task_load(
    params: TaskLoadParams,
    *,
    settings: Settings,
    client: httpx.AsyncClient | None = None,
    publisher: RabbitPublisher | None = None,
) -> ScenarioResult:
    """`task_load` senaryosunu çalıştırır.

    `client` ve `publisher` test'ten enjekte edilebilir; default'ta
    `httpx.AsyncClient` veya `AioPikaPublisher` üretilir.
    """
    if params.target == "rabbit":
        if client is not None:
            raise ValueError(
                "target='rabbit' iken `client` parametresi gönderilemez."
            )
        return await _run_rabbit(params, settings, publisher=publisher)

    if publisher is not None:
        raise ValueError(
            "target='rest' iken `publisher` parametresi gönderilemez."
        )
    return await _run_rest(params, settings, client=client)


def run_task_load_sync(
    params: TaskLoadParams, *, settings: Settings
) -> ScenarioResult:
    """CLI için sync sarmalayıcı."""
    return asyncio.run(run_task_load(params, settings=settings))


# Test/CLI yardımcısı — InMemoryRabbitPublisher'ı dışarı açar
__all__ = [
    "TaskLoadParams",
    "run_task_load",
    "run_task_load_sync",
    "InMemoryRabbitPublisher",
]
