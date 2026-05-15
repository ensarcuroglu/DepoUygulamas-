"""`agv_traffic` senaryosu — Backend yerleştirme uçlarına yoğun trafik.

Faz 0 kararı (envanter §3): AgvSimService'e doğrudan istek atılmaz.
Yalnızca ``POST /api/yerlestirme-gorevleri/`` çağrısı yapılır; backend
kendi ``HttpAgvDispatcher`` üzerinden AgvSim'i tetikler ve AgvSim
``POST /api/agv-callbacks/gorev-tamamlandi`` ile geri yazar. WMS state
bütünlüğü bu sayede korunur.

ID havuzu stratejisi:
  Backend'de seed_baseline (veya `seed.py`) sonucu mevcut palet ve raf
  ID'leri bilinir; bu senaryo ``palet_id_min..palet_id_max`` ve
  ``raf_id_min..raf_id_max`` aralıklarını parametre olarak alır.
  Daha gelişmiş kullanım için ileride `GET /api/paletler/` ile fetch
  eklenebilir; MVP'de range yeterli.

Öncelik dağılımı (saha profiline yakın):
  oncelik=1 (acil)  %20
  oncelik=3 (normal) %60
  oncelik=5 (düşük)  %20
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import httpx

from app.core.config import Settings
from app.factories import ReferenceTable, YerlestirmeGorevFactory
from app.infrastructure.auth import JwtAuthClient
from app.infrastructure.emitters import RestEmitter

from .target_matrix import validate_target
from .timeseries_history import ScenarioResult

log = logging.getLogger("data-gen.scenario.agv_traffic")

AgvTrafficTarget = Literal["rest"]


@dataclass(frozen=True)
class AgvTrafficParams:
    """`agv_traffic` parametreleri."""

    count: int = 500
    seed: int = 42
    target: AgvTrafficTarget = "rest"
    palet_id_min: int = 1
    palet_id_max: int = 1_000
    raf_id_min: int = 1
    raf_id_max: int = 300
    batch_size: int = 100
    concurrency: int = 10

    def __post_init__(self) -> None:
        validate_target("agv_traffic", self.target)
        if self.count < 1:
            raise ValueError("count >= 1 olmalı")
        if self.palet_id_min < 1 or self.palet_id_max < self.palet_id_min:
            raise ValueError(
                "palet_id aralığı geçersiz; min>=1 ve max>=min olmalı"
            )
        if self.raf_id_min < 1 or self.raf_id_max < self.raf_id_min:
            raise ValueError(
                "raf_id aralığı geçersiz; min>=1 ve max>=min olmalı"
            )
        if self.batch_size < 1:
            raise ValueError("batch_size >= 1 olmalı")
        if self.concurrency < 1:
            raise ValueError("concurrency >= 1 olmalı")


def _chunks(items: Sequence, size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _id_pool(start: int, end_inclusive: int) -> ReferenceTable:
    pool = ReferenceTable()
    for i in range(start, end_inclusive + 1):
        pool.add({"id": i})
    return pool


async def run_agv_traffic(
    params: AgvTrafficParams,
    *,
    settings: Settings,
    client: httpx.AsyncClient | None = None,
) -> ScenarioResult:
    """`agv_traffic` senaryosunu çalıştırır.

    Args:
        params: Senaryo parametreleri (target='rest' zorlanmış).
        settings: Runtime config (backend URL, credentials).
        client: Test'ten enjekte edilebilir; None ise burada üretilir.
    """
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

        palet_pool = _id_pool(params.palet_id_min, params.palet_id_max)
        raf_pool = _id_pool(params.raf_id_min, params.raf_id_max)

        factory = YerlestirmeGorevFactory(
            seed=params.seed, palet_pool=palet_pool, raf_pool=raf_pool
        )
        # Saha profiline yakın öncelik dağılımı için weighted oncelik üret.
        gorevler = [
            factory.build_one(i, oncelik=_weighted_oncelik(i, params.seed))
            for i in range(params.count)
        ]

        emitter = RestEmitter(
            client=client,
            path="/api/yerlestirme-gorevleri/",
            auth=auth,
            semaphore=semaphore,
        )
        for batch in _chunks(gorevler, params.batch_size):
            await emitter.emit_batch(batch)

        summary = emitter.summary()
        log.info(
            "agv_traffic: total=%d success=%d failed=%d duration=%.2fs p95=%.2fms",
            summary.total,
            summary.success,
            summary.failed,
            summary.duration_sec,
            summary.p95_latency_ms,
        )
        return ScenarioResult(
            scenario="agv_traffic",
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


def _weighted_oncelik(index: int, seed: int) -> int:
    """Deterministik öncelik (saha profili: 20% acil / 60% normal / 20% düşük)."""
    # Basit deterministik hash; seed'den bağımsız sıralı index'le karıştır.
    bucket = (index * 2654435761 + seed) % 100
    if bucket < 20:
        return 1
    if bucket < 80:
        return 3
    return 5


def run_agv_traffic_sync(
    params: AgvTrafficParams, *, settings: Settings
) -> ScenarioResult:
    """CLI için sync sarmalayıcı."""
    return asyncio.run(run_agv_traffic(params, settings=settings))


__all__ = ["AgvTrafficParams", "run_agv_traffic", "run_agv_traffic_sync"]
