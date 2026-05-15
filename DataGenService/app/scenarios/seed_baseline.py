"""`seed_baseline` senaryosu — Backend'e referans havuzu basar.

Backend'de **kategori/marka/tedarikçi/depo/zon** seed verisinin halihazırda
mevcut olduğu varsayılır (`BackendProje/seed.py` veya `dev_seed_minimal.sql`).
Bu senaryo şu zinciri ekler:

    Raf → Ürün → Lot → Palet

FK bağımlılıkları sebebiyle bu sırada yayın yapılır. Her aşamada backend'in
döndürdüğü `id` referans havuza eklenir; sonraki aşama oradan seçer.

Idempotency-Key: CRUD uçları (paletler/lotlar/raflar/ürünler) backend'de
şu an Idempotency-Key desteklemez (envanter §1.1). Re-run'da `409`/`422`
duplicate barkod/kod hataları beklenir; `failed` sayar, akış devam eder.
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
    LotFactory,
    PaletFactory,
    RafFactory,
    ReferenceTable,
    UrunFactory,
)
from app.infrastructure.auth import JwtAuthClient
from app.infrastructure.emitters import RestEmitter

from .timeseries_history import ScenarioResult

log = logging.getLogger("data-gen.scenario.seed_baseline")

ScenarioTarget = Literal["rest"]


@dataclass(frozen=True)
class SeedBaselineParams:
    """`seed_baseline` parametreleri."""

    urun_count: int = 1_000
    raf_count: int = 300
    lot_count: int = 2_000
    palet_count: int = 10_000
    seed: int = 42
    target: ScenarioTarget = "rest"
    # Backend seed verisinden gelen FK varsayımları
    mevcut_depo_id: int = 1
    batch_size: int = 500
    concurrency: int = 10

    def __post_init__(self) -> None:
        if self.target != "rest":
            raise ValueError(
                "seed_baseline yalnız target='rest' destekler (hedef matrisi)."
            )
        for ad, deg in (
            ("urun_count", self.urun_count),
            ("raf_count", self.raf_count),
            ("lot_count", self.lot_count),
            ("palet_count", self.palet_count),
            ("batch_size", self.batch_size),
            ("concurrency", self.concurrency),
        ):
            if deg < 1:
                raise ValueError(f"{ad} >= 1 olmalı (alındı: {deg})")


def _chunks(items: Sequence, size: int):
    for start in range(0, len(items), size):
        yield items[start : start + size]


def _id_havuz(emitter_sonuc: list[dict | None], dto_list) -> ReferenceTable:
    """Sıralı response → ReferenceTable. Hatalı slot'lar atlanır."""
    pool = ReferenceTable()
    for resp, dto in zip(emitter_sonuc, dto_list):
        if isinstance(resp, dict) and "id" in resp:
            pool.add({"id": int(resp["id"]), **dto.model_dump()})
    return pool


async def run_seed_baseline(
    params: SeedBaselineParams,
    *,
    settings: Settings,
    client: httpx.AsyncClient | None = None,
) -> ScenarioResult:
    """`seed_baseline` senaryosunu çalıştırır.

    Args:
        params: Senaryo parametreleri.
        settings: DataGenService runtime config (backend URL, credentials).
        client: Test'ten enjekte edilebilecek `httpx.AsyncClient`. None ise
                burada üretilir ve kapatılır.
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

        # 1) Raflar (depo_id sabitlenir)
        raf_dtos = RafFactory(seed=params.seed).build_many(
            params.raf_count, depo_id=params.mevcut_depo_id
        )
        raf_emitter = RestEmitter(
            client=client, path="/api/raflar/", auth=auth, semaphore=semaphore
        )
        raf_resp = await _yayinla(raf_emitter, raf_dtos, params.batch_size)
        raf_pool = _id_havuz(raf_resp, raf_dtos)
        log.info(
            "raflar: %d/%d başarılı", len(raf_pool), params.raf_count
        )

        # 2) Ürünler
        urun_dtos = UrunFactory(seed=params.seed).build_many(params.urun_count)
        urun_emitter = RestEmitter(
            client=client, path="/api/urunler/", auth=auth, semaphore=semaphore
        )
        urun_resp = await _yayinla(urun_emitter, urun_dtos, params.batch_size)
        urun_pool = _id_havuz(urun_resp, urun_dtos)
        log.info(
            "ürünler: %d/%d başarılı", len(urun_pool), params.urun_count
        )

        if len(urun_pool) == 0:
            raise RuntimeError(
                "Hiç ürün eklenmedi; lot/palet aşamasına geçilemez. "
                "Backend log'larını inceleyin."
            )

        # 3) Lotlar (urun_pool gerekli)
        lot_dtos = LotFactory(seed=params.seed, urun_pool=urun_pool).build_many(
            params.lot_count
        )
        lot_emitter = RestEmitter(
            client=client, path="/api/lotlar/", auth=auth, semaphore=semaphore
        )
        lot_resp = await _yayinla(lot_emitter, lot_dtos, params.batch_size)
        lot_pool = _id_havuz(lot_resp, lot_dtos)
        log.info("lotlar: %d/%d başarılı", len(lot_pool), params.lot_count)

        if len(lot_pool) == 0 or len(raf_pool) == 0:
            raise RuntimeError(
                "lot veya raf havuzu boş; palet aşamasına geçilemez."
            )

        # 4) Paletler (lot_pool + raf_pool gerekli)
        palet_dtos = PaletFactory(
            seed=params.seed, lot_pool=lot_pool, raf_pool=raf_pool
        ).build_many(params.palet_count)
        palet_emitter = RestEmitter(
            client=client,
            path="/api/paletler/",
            auth=auth,
            semaphore=semaphore,
        )
        await _yayinla(palet_emitter, palet_dtos, params.batch_size)
        log.info(
            "paletler: %d/%d başarılı",
            palet_emitter.summary().success,
            params.palet_count,
        )

        # Toplu özet (basit toplama)
        emitters = [raf_emitter, urun_emitter, lot_emitter, palet_emitter]
        toplam = sum(e.summary().total for e in emitters)
        basarili = sum(e.summary().success for e in emitters)
        hatali = sum(e.summary().failed for e in emitters)
        sure = max(e.summary().duration_sec for e in emitters)
        # Tüm latency'leri birleştirip p95 hesapla
        tum_latency = [
            ms for e in emitters for ms in e.summary().latencies_ms
        ]
        if tum_latency:
            tum_latency.sort()
            p95 = tum_latency[max(0, int(0.95 * len(tum_latency)) - 1)]
        else:
            p95 = 0.0
        hatalar = [err for e in emitters for err in e.summary().errors[:3]]

        return ScenarioResult(
            scenario="seed_baseline",
            output_path=None,
            total=toplam,
            success=basarili,
            failed=hatali,
            duration_sec=sure,
            p95_latency_ms=p95,
            errors=hatalar[:5],
        )
    finally:
        if own_client:
            await client.aclose()


async def _yayinla(
    emitter: RestEmitter, dtos, batch_size: int
) -> list[dict | None]:
    """DTO listesini batch'lere bölüp emitter ile yayar; sıralı response döner."""
    responses: list[dict | None] = []
    for batch in _chunks(list(dtos), batch_size):
        responses.extend(await emitter.emit_batch_with_responses(batch))
    return responses


def run_seed_baseline_sync(
    params: SeedBaselineParams,
    *,
    settings: Settings,
) -> ScenarioResult:
    """CLI için sync sarmalayıcı."""
    return asyncio.run(run_seed_baseline(params, settings=settings))
