"""API ve CLI için ortak senaryo çalıştırıcı.

Faz 7'nin amacı senaryo implementasyonlarını değiştirmeden aynı küçük
parametre yüzeyini (`count`, `seed`, `target`, `batch_size`, `concurrency`)
hem HTTP hem CLI üzerinden kullanmaktır.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import Settings, get_settings
from app.infrastructure.emitters import RabbitPublisher

from .agv_traffic import AgvTrafficParams, run_agv_traffic
from .seed_baseline import SeedBaselineParams, run_seed_baseline
from .target_matrix import DEFAULT_TARGET, TargetNotAllowedError, validate_target
from .task_load import TaskLoadParams, run_task_load
from .timeseries_history import (
    ScenarioResult,
    TimeseriesHistoryParams,
    run_timeseries_history,
)

DEFAULT_TIMESERIES_GUN_SAYISI = 30
DEFAULT_TIMESERIES_URUN_COUNT = 1_000

_SEED_BASELINE_DEFAULT_COUNTS: dict[str, int] = {
    "raf_count": 300,
    "urun_count": 1_000,
    "lot_count": 2_000,
    "palet_count": 10_000,
}


class ScenarioRunRequest(BaseModel):
    """API/CLI tarafından kullanılan ortak çalıştırma parametreleri."""

    model_config = ConfigDict(extra="forbid")

    count: int | None = Field(default=None, ge=1)
    seed: int | None = None
    target: str | None = None
    batch_size: int | None = Field(default=None, ge=1)
    concurrency: int | None = Field(default=None, ge=1)


def _resolve_target(scenario: str, target: str | None) -> str:
    if scenario not in DEFAULT_TARGET:
        raise TargetNotAllowedError(f"Bilinmeyen senaryo: {scenario!r}")
    resolved = target or DEFAULT_TARGET[scenario]
    validate_target(scenario, resolved)
    return resolved


def _seed_baseline_counts(total_count: int | None) -> dict[str, int]:
    """Generic `count` değerini raf/ürün/lot/palet oranlarına böler.

    `count` verilmezse senaryonun kendi MVP default'ları kullanılır. Verilirse
    değer toplam seed denemesi olarak ele alınır; FK zinciri sebebiyle 1-3 gibi
    çok küçük değerlerde her aşamadan en az bir kayıt üretilir.
    """

    if total_count is None:
        return {}

    if total_count <= len(_SEED_BASELINE_DEFAULT_COUNTS):
        return {name: 1 for name in _SEED_BASELINE_DEFAULT_COUNTS}

    minimums = {name: 1 for name in _SEED_BASELINE_DEFAULT_COUNTS}
    remaining = total_count - sum(minimums.values())
    default_total = sum(_SEED_BASELINE_DEFAULT_COUNTS.values())

    raw_parts = {
        name: remaining * default / default_total
        for name, default in _SEED_BASELINE_DEFAULT_COUNTS.items()
    }
    counts = {
        name: minimums[name] + int(raw)
        for name, raw in raw_parts.items()
    }

    missing = total_count - sum(counts.values())
    by_remainder = sorted(
        raw_parts.items(),
        key=lambda item: item[1] - int(item[1]),
        reverse=True,
    )
    for name, _raw in by_remainder[:missing]:
        counts[name] += 1

    return counts


async def run_scenario(
    scenario: str,
    request: ScenarioRunRequest,
    *,
    settings: Settings | None = None,
    client: httpx.AsyncClient | None = None,
    publisher: RabbitPublisher | None = None,
) -> ScenarioResult:
    """Senaryoyu ortak API/CLI parametreleriyle çalıştırır."""

    settings = settings or get_settings()
    target = _resolve_target(scenario, request.target)
    seed = request.seed if request.seed is not None else settings.default_seed
    batch_size = request.batch_size or settings.batch_size
    concurrency = request.concurrency or settings.concurrency

    if scenario == "seed_baseline":
        if publisher is not None:
            raise ValueError("seed_baseline için `publisher` gönderilemez.")
        params = SeedBaselineParams(
            seed=seed,
            target=target,  # type: ignore[arg-type]
            batch_size=batch_size,
            concurrency=concurrency,
            **_seed_baseline_counts(request.count),
        )
        return await run_seed_baseline(params, settings=settings, client=client)

    if scenario == "task_load":
        params = TaskLoadParams(
            count=request.count or TaskLoadParams().count,
            seed=seed,
            target=target,  # type: ignore[arg-type]
            batch_size=batch_size,
            concurrency=concurrency,
        )
        return await run_task_load(
            params, settings=settings, client=client, publisher=publisher
        )

    if scenario == "timeseries_history":
        if client is not None or publisher is not None:
            raise ValueError(
                "timeseries_history için `client` veya `publisher` gönderilemez."
            )
        params = TimeseriesHistoryParams(
            gun_sayisi=DEFAULT_TIMESERIES_GUN_SAYISI,
            urun_count=request.count or DEFAULT_TIMESERIES_URUN_COUNT,
            seed=seed,
            target=target,  # type: ignore[arg-type]
            output_dir=settings.output_dir,
            batch_size=batch_size,
        )
        return await run_timeseries_history(
            params, default_output_dir=settings.output_dir
        )

    if scenario == "agv_traffic":
        if publisher is not None:
            raise ValueError("agv_traffic için `publisher` gönderilemez.")
        params = AgvTrafficParams(
            count=request.count or AgvTrafficParams().count,
            seed=seed,
            target=target,  # type: ignore[arg-type]
            batch_size=batch_size,
            concurrency=concurrency,
        )
        return await run_agv_traffic(params, settings=settings, client=client)

    # _resolve_target bu yolu zaten kapatır; tip denetleyici ve savunmacılık için.
    raise TargetNotAllowedError(f"Bilinmeyen senaryo: {scenario!r}")


def run_scenario_sync(
    scenario: str,
    request: ScenarioRunRequest,
    *,
    settings: Settings | None = None,
) -> ScenarioResult:
    """CLI için senkron sarmalayıcı."""

    import asyncio

    return asyncio.run(run_scenario(scenario, request, settings=settings))


def result_to_jsonable(result: ScenarioResult) -> dict[str, Any]:
    """FastAPI ve CLI çıktısında kullanılan JSON özet."""

    return result.to_dict()
