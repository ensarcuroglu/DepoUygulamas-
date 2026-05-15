"""Senaryo × hedef izin matrisi (tek doğruluk kaynağı).

Faz 7'de API ve CLI bu sözlüğü tüketir. İzinsiz kombinasyon `422` ile reddedilir.

Detay: `DataGenService/docs/endpoint_envanteri.md` §4.
"""

from __future__ import annotations

from typing import Final, Literal

ScenarioName = Literal[
    "seed_baseline",
    "task_load",
    "timeseries_history",
    "agv_traffic",
]
TargetName = Literal["rest", "rabbit", "file"]


ALLOWED_TARGETS: Final[dict[ScenarioName, frozenset[TargetName]]] = {
    "seed_baseline": frozenset({"rest"}),
    "task_load": frozenset({"rest", "rabbit"}),
    "timeseries_history": frozenset({"rest", "file"}),
    "agv_traffic": frozenset({"rest"}),
}

DEFAULT_TARGET: Final[dict[ScenarioName, TargetName]] = {
    "seed_baseline": "rest",
    "task_load": "rest",
    "timeseries_history": "file",
    "agv_traffic": "rest",
}


class TargetNotAllowedError(ValueError):
    """Senaryo + target kombinasyonu izinsiz."""


def validate_target(scenario: str, target: str) -> None:
    """`scenario × target` kombinasyonu izinli mi? Değilse hata fırlatır."""
    if scenario not in ALLOWED_TARGETS:
        raise TargetNotAllowedError(f"Bilinmeyen senaryo: {scenario!r}")
    if target not in ALLOWED_TARGETS[scenario]:
        izinli = sorted(ALLOWED_TARGETS[scenario])
        raise TargetNotAllowedError(
            f"Senaryo {scenario!r} için target {target!r} izinli değil. "
            f"İzinli: {izinli}"
        )
