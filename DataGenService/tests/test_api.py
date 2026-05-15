"""Faz 7 — Senaryo API testleri."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.scenarios import ScenarioResult
from app.scenarios.runner import ScenarioRunRequest


@pytest.mark.unit
def test_scenario_api_runs_all_scenarios_via_common_runner(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """HTTP yüzeyi dört senaryoyu aynı request modeliyle runner'a taşır."""
    from app.api.routers import scenarios as scenarios_router

    calls: list[tuple[str, int | None, int | None, str | None]] = []

    async def fake_run_scenario(
        name: str, body: ScenarioRunRequest, *, settings: object
    ) -> ScenarioResult:
        calls.append((name, body.count, body.seed, body.target))
        return ScenarioResult(
            scenario=name,
            output_path=None,
            total=body.count or 1,
            success=body.count or 1,
            failed=0,
            duration_sec=0.01,
            p95_latency_ms=1.0,
        )

    monkeypatch.setattr(scenarios_router, "run_scenario", fake_run_scenario)

    for name, target in (
        ("seed_baseline", "rest"),
        ("task_load", "rabbit"),
        ("timeseries_history", "file"),
        ("agv_traffic", "rest"),
    ):
        response = client.post(
            f"/scenarios/{name}/run",
            json={
                "count": 3,
                "seed": 7,
                "target": target,
                "batch_size": 2,
                "concurrency": 1,
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["scenario"] == name
        assert payload["total"] == 3
        assert payload["success"] == 3
        assert payload["failed"] == 0

    assert calls == [
        ("seed_baseline", 3, 7, "rest"),
        ("task_load", 3, 7, "rabbit"),
        ("timeseries_history", 3, 7, "file"),
        ("agv_traffic", 3, 7, "rest"),
    ]


@pytest.mark.unit
def test_scenario_api_rejects_disallowed_target(client: TestClient) -> None:
    response = client.post(
        "/scenarios/agv_traffic/run",
        json={"count": 1, "target": "file"},
    )

    assert response.status_code == 422
    assert "izinli değil" in response.json()["detail"]


@pytest.mark.unit
def test_scenario_api_runs_timeseries_file_actual(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Default file target gerçek emitter ile küçük parquet üretir."""
    monkeypatch.setenv("OUTPUT_DIR", str(tmp_path))
    get_settings.cache_clear()

    from main import app

    with TestClient(app) as local_client:
        response = local_client.post(
            "/scenarios/timeseries_history/run",
            json={"count": 2, "seed": 11, "batch_size": 5},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scenario"] == "timeseries_history"
    assert payload["total"] == 60
    assert payload["success"] == 60
    assert payload["failed"] == 0
    assert payload["output_path"]
    assert Path(payload["output_path"]).exists()
