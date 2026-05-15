"""Faz 4 — Senaryo × hedef izin matrisi testleri."""

from __future__ import annotations

import pytest

from app.scenarios import (
    ALLOWED_TARGETS,
    DEFAULT_TARGET,
    TargetNotAllowedError,
    validate_target,
)


@pytest.mark.unit
def test_seed_baseline_only_accepts_rest() -> None:
    assert ALLOWED_TARGETS["seed_baseline"] == frozenset({"rest"})
    validate_target("seed_baseline", "rest")
    for bad in ("rabbit", "file"):
        with pytest.raises(TargetNotAllowedError):
            validate_target("seed_baseline", bad)


@pytest.mark.unit
def test_task_load_accepts_rest_and_rabbit() -> None:
    assert ALLOWED_TARGETS["task_load"] == frozenset({"rest", "rabbit"})
    validate_target("task_load", "rest")
    validate_target("task_load", "rabbit")
    with pytest.raises(TargetNotAllowedError):
        validate_target("task_load", "file")


@pytest.mark.unit
def test_timeseries_history_accepts_file_and_rest() -> None:
    assert ALLOWED_TARGETS["timeseries_history"] == frozenset({"rest", "file"})
    validate_target("timeseries_history", "file")
    validate_target("timeseries_history", "rest")
    with pytest.raises(TargetNotAllowedError):
        validate_target("timeseries_history", "rabbit")


@pytest.mark.unit
def test_agv_traffic_only_accepts_rest() -> None:
    assert ALLOWED_TARGETS["agv_traffic"] == frozenset({"rest"})
    validate_target("agv_traffic", "rest")
    for bad in ("rabbit", "file"):
        with pytest.raises(TargetNotAllowedError):
            validate_target("agv_traffic", bad)


@pytest.mark.unit
def test_unknown_scenario_rejected() -> None:
    with pytest.raises(TargetNotAllowedError, match="Bilinmeyen senaryo"):
        validate_target("yok_boyle_senaryo", "rest")


@pytest.mark.unit
def test_default_targets_are_in_allowed_set() -> None:
    """Her senaryonun default target'ı izinli kümede olmalı."""
    for senaryo, default in DEFAULT_TARGET.items():
        assert default in ALLOWED_TARGETS[senaryo]


@pytest.mark.unit
def test_seed_baseline_params_rejects_non_rest() -> None:
    from app.scenarios import SeedBaselineParams

    SeedBaselineParams(target="rest")  # OK
    with pytest.raises(ValueError, match="target='rest'"):
        SeedBaselineParams(target="file")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="target='rest'"):
        SeedBaselineParams(target="rabbit")  # type: ignore[arg-type]
