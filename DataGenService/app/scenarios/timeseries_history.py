"""`timeseries_history` senaryosu — ML eğitim verisi (default file emitter).

Akış:
  1. `UrunFactory(seed)` ile P ürün üret.
  2. `TalepZamanSerisiFactory(seed, urun_pool)` ile P × T satır yayını.
  3. Hedef = `file`: parquet/csv. Hedef = `rest`: Faz 4'te eklenecek (NotImplemented).

Çıktı dosya adı: ``talep_gecmis_{baslangic:%Y%m%d}_{seed}.parquet``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterator, Literal

from app.factories import (
    ReferenceTable,
    TalepGecmisKaydiDTO,
    TalepZamanSerisiFactory,
    UrunFactory,
)
from app.infrastructure.emitters import FileEmitter, FileFormat

ScenarioTarget = Literal["file", "rest"]


@dataclass(frozen=True)
class TimeseriesHistoryParams:
    """`timeseries_history` parametreleri."""

    gun_sayisi: int
    urun_count: int = 1_000
    seed: int = 42
    baslangic: date = date(2024, 1, 1)
    target: ScenarioTarget = "file"
    file_format: FileFormat = "parquet"
    output_dir: Path | None = None
    batch_size: int = 5_000

    def __post_init__(self) -> None:
        if self.gun_sayisi < 1:
            raise ValueError("gun_sayisi >= 1 olmalı")
        if self.urun_count < 1:
            raise ValueError("urun_count >= 1 olmalı")
        if self.batch_size < 1:
            raise ValueError("batch_size >= 1 olmalı")
        if self.target == "rest":
            raise NotImplementedError(
                "target='rest' Faz 4'te eklenecek; şu an yalnız 'file' destekli."
            )


@dataclass
class ScenarioResult:
    """Senaryo çalıştırma özeti."""

    scenario: str
    output_path: Path | None
    total: int
    success: int
    failed: int
    duration_sec: float
    p95_latency_ms: float
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario": self.scenario,
            "output_path": str(self.output_path) if self.output_path else None,
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "duration_sec": round(self.duration_sec, 3),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "errors": self.errors[:5],
        }


def _build_urun_pool(seed: int, count: int) -> ReferenceTable:
    pool = ReferenceTable()
    for i, dto in enumerate(UrunFactory(seed=seed).build_many(count), start=1):
        pool.add({"id": i, **dto.model_dump()})
    return pool


def _chunk_iter(
    items: Iterator[TalepGecmisKaydiDTO], size: int
) -> Iterator[list[TalepGecmisKaydiDTO]]:
    """Generator'ı sabit boyutlu listelere bölen yardımcı."""
    buffer: list[TalepGecmisKaydiDTO] = []
    for item in items:
        buffer.append(item)
        if len(buffer) >= size:
            yield buffer
            buffer = []
    if buffer:
        yield buffer


def _default_output_path(
    output_dir: Path, params: TimeseriesHistoryParams
) -> Path:
    suffix = "parquet" if params.file_format == "parquet" else "csv"
    name = (
        f"talep_gecmis_{params.baslangic:%Y%m%d}_seed{params.seed}_"
        f"u{params.urun_count}_g{params.gun_sayisi}.{suffix}"
    )
    return output_dir / name


async def run_timeseries_history(
    params: TimeseriesHistoryParams,
    *,
    default_output_dir: Path | None = None,
) -> ScenarioResult:
    """`timeseries_history` senaryosunu çalıştırır.

    Args:
        params: Çalıştırma parametreleri.
        default_output_dir: `params.output_dir` None ise kullanılan dizin.
                            Tipik olarak `Settings.output_dir` enjekte edilir.
    """
    output_dir = params.output_dir or default_output_dir
    if output_dir is None:
        raise ValueError(
            "output_dir verilmedi ve default_output_dir tanımlı değil."
        )

    output_path = _default_output_path(Path(output_dir), params)
    urun_pool = _build_urun_pool(params.seed, params.urun_count)
    factory = TalepZamanSerisiFactory(
        seed=params.seed,
        urun_pool=urun_pool,
        baslangic=params.baslangic,
    )

    series = factory.build_series(gun_sayisi=params.gun_sayisi)
    async with FileEmitter(output_path, file_format=params.file_format) as emitter:
        for batch in _chunk_iter(series, params.batch_size):
            await emitter.emit_batch(batch)
        # close __aexit__ tarafından çağrılacak
    summary = emitter.summary()

    return ScenarioResult(
        scenario="timeseries_history",
        output_path=output_path,
        total=summary.total,
        success=summary.success,
        failed=summary.failed,
        duration_sec=summary.duration_sec,
        p95_latency_ms=summary.p95_latency_ms,
        errors=summary.errors,
    )


def run_timeseries_history_sync(
    params: TimeseriesHistoryParams,
    *,
    default_output_dir: Path | None = None,
) -> ScenarioResult:
    """CLI için sync sarmalayıcı."""
    return asyncio.run(
        run_timeseries_history(params, default_output_dir=default_output_dir)
    )
