"""Faz 7 — Typer CLI testleri."""

from __future__ import annotations

import json

import pytest
from typer.testing import CliRunner

import cli
from app.scenarios import ScenarioResult
from app.scenarios.runner import ScenarioRunRequest


@pytest.mark.unit
def test_cli_run_outputs_json_for_all_scenarios(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = CliRunner()
    calls: list[tuple[str, int | None, int | None, str | None]] = []

    def fake_run_scenario_sync(
        scenario: str,
        request: ScenarioRunRequest,
        *,
        settings: object,
    ) -> ScenarioResult:
        calls.append((scenario, request.count, request.seed, request.target))
        return ScenarioResult(
            scenario=scenario,
            output_path=None,
            total=request.count or 1,
            success=request.count or 1,
            failed=0,
            duration_sec=0.01,
            p95_latency_ms=1.0,
        )

    monkeypatch.setattr(cli, "run_scenario_sync", fake_run_scenario_sync)

    for scenario, target in (
        ("seed_baseline", "rest"),
        ("task_load", "rabbit"),
        ("timeseries_history", "file"),
        ("agv_traffic", "rest"),
    ):
        result = runner.invoke(
            cli.app,
            [
                "run",
                scenario,
                "--count",
                "4",
                "--seed",
                "99",
                "--target",
                target,
                "--batch-size",
                "2",
                "--concurrency",
                "1",
            ],
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["scenario"] == scenario
        assert payload["total"] == 4
        assert payload["success"] == 4

    assert calls == [
        ("seed_baseline", 4, 99, "rest"),
        ("task_load", 4, 99, "rabbit"),
        ("timeseries_history", 4, 99, "file"),
        ("agv_traffic", 4, 99, "rest"),
    ]


@pytest.mark.unit
def test_cli_rejects_disallowed_target() -> None:
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        ["run", "agv_traffic", "--target", "file"],
    )

    assert result.exit_code == 2
    assert "izinli değil" in result.output


@pytest.mark.unit
def test_datagen_module_exposes_typer_app() -> None:
    from datagen import app as datagen_app

    runner = CliRunner()
    result = runner.invoke(datagen_app, ["--help"])

    assert result.exit_code == 0
    assert "DataGenService CLI" in result.output

