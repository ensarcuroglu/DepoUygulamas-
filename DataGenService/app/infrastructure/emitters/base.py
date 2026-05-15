"""Emitter sözleşmesi — file / rest / rabbit hepsi aynı arayüzü implement eder.

Her senaryo, ürettiği Pydantic DTO'ları batch'ler halinde emitter'a yollar.
Emitter:
  - emit_batch(items)        — N kayıt yaz/yayinla
  - close()                  — kaynakları kapat, buffer'ı flush et
  - summary() -> EmitSummary — toplam/başarı/hata/süre/p95 latency

Tüm emitter'lar `async def emit_batch` ve `async def close` sağlar; sync
backend kullansalar bile signature async kalır (REST/Rabbit ile aynı kalıp).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Protocol, Sequence

from pydantic import BaseModel


@dataclass
class EmitSummary:
    """Senaryo sonu özet metrikleri."""

    total: int = 0
    success: int = 0
    failed: int = 0
    started_at: float = field(default_factory=time.perf_counter)
    ended_at: float | None = None
    latencies_ms: list[float] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def duration_sec(self) -> float:
        end = self.ended_at if self.ended_at is not None else time.perf_counter()
        return max(0.0, end - self.started_at)

    @property
    def p95_latency_ms(self) -> float:
        if not self.latencies_ms:
            return 0.0
        sorted_lat = sorted(self.latencies_ms)
        # 95. yüzdelik (interpolasyonsuz, küçük örneklemde yeterli).
        idx = max(0, int(0.95 * len(sorted_lat)) - 1)
        return sorted_lat[idx]

    def to_dict(self) -> dict[str, object]:
        return {
            "total": self.total,
            "success": self.success,
            "failed": self.failed,
            "duration_sec": round(self.duration_sec, 3),
            "p95_latency_ms": round(self.p95_latency_ms, 2),
            "error_sample": self.errors[:5],
        }

    def mark_finished(self) -> None:
        if self.ended_at is None:
            self.ended_at = time.perf_counter()


class IEmitter(Protocol):
    """Senaryo → backend/dosya yayını için uniform arayüz."""

    async def emit_batch(self, items: Sequence[BaseModel]) -> None: ...

    async def close(self) -> None: ...

    def summary(self) -> EmitSummary: ...
