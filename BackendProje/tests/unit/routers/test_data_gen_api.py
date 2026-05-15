"""Router testleri: app.api.v1.routers.data_gen."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.api.v1.routers import data_gen as data_gen_router
from app.core.config import get_settings
from app.infrastructure.services.data_gen_client import (
    DataGenClientTimeoutError,
    DataGenClientUnavailableError,
    DataGenClientUpstreamError,
)
from main import app

pytestmark = pytest.mark.api


class FakeDataGenClient:
    def __init__(self):
        self.calls = []

    def healthz(self):
        return {"status": "ok", "service": "data-gen"}

    def run_scenario(self, name, payload):
        self.calls.append((name, payload))
        return {
            "scenario": name,
            "output_path": None,
            "total": payload.get("count", 1),
            "success": payload.get("count", 1),
            "failed": 0,
            "duration_sec": 0.01,
            "p95_latency_ms": 1.0,
            "errors": [],
        }


def _set_client(fake):
    app.dependency_overrides[data_gen_router._get_client] = lambda: fake


def test_metadata_returns_static_scenarios(client, admin_user):
    fake = FakeDataGenClient()
    _set_client(fake)

    resp = client.get("/api/data-gen/metadata")

    assert resp.status_code == 200, resp.text
    data = resp.json()
    names = {item["name"] for item in data["scenarios"]}
    assert names == {"seed_baseline", "task_load", "timeseries_history", "agv_traffic"}
    timeseries = next(item for item in data["scenarios"] if item["name"] == "timeseries_history")
    assert timeseries["allowed_targets"] == ["file"]


def test_healthz_forwards_to_client(client, admin_user):
    fake = FakeDataGenClient()
    _set_client(fake)

    resp = client.get("/api/data-gen/healthz")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "data-gen"}


def test_run_scenario_forwards_body_and_default_target(client, admin_user):
    fake = FakeDataGenClient()
    _set_client(fake)

    resp = client.post(
        "/api/data-gen/scenarios/timeseries_history/run",
        json={"count": 2, "seed": 11, "batch_size": 5},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["scenario"] == "timeseries_history"
    assert fake.calls == [
        (
            "timeseries_history",
            {"count": 2, "seed": 11, "batch_size": 5, "target": "file"},
        )
    ]


def test_run_scenario_rejects_disallowed_target(client, admin_user):
    fake = FakeDataGenClient()
    _set_client(fake)

    resp = client.post(
        "/api/data-gen/scenarios/agv_traffic/run",
        json={"count": 1, "target": "file"},
    )

    assert resp.status_code == 422
    assert "izinli" in resp.json()["detail"]
    assert fake.calls == []


def test_upstream_501_is_standardized(client, admin_user):
    class FailingClient(FakeDataGenClient):
        def run_scenario(self, name, payload):
            raise DataGenClientUpstreamError(501, "rest destekli degil")

    _set_client(FailingClient())

    resp = client.post(
        "/api/data-gen/scenarios/task_load/run",
        json={"count": 1, "target": "rest"},
    )

    assert resp.status_code == 501
    assert resp.json()["success"] is False
    assert "rest destekli degil" in resp.json()["error"]


def test_timeout_is_504(client, admin_user):
    class TimeoutClient(FakeDataGenClient):
        def healthz(self):
            raise DataGenClientTimeoutError("DataGenService zaman asimina ugradi.", 504)

    _set_client(TimeoutClient())

    resp = client.get("/api/data-gen/healthz")

    assert resp.status_code == 504


def test_unavailable_is_503(client, admin_user):
    class UnavailableClient(FakeDataGenClient):
        def healthz(self):
            raise DataGenClientUnavailableError("DataGenService'e ulasilamiyor.", 503)

    _set_client(UnavailableClient())

    resp = client.get("/api/data-gen/healthz")

    assert resp.status_code == 503


def test_feature_disabled_returns_404(client, admin_user):
    app.dependency_overrides[get_settings] = lambda: SimpleNamespace(
        feature_data_gen_enabled=False,
        data_gen_service_url="http://data-gen.test",
        data_gen_service_timeout=5.0,
    )

    resp = client.get("/api/data-gen/metadata")

    assert resp.status_code == 404
    assert "devre disi" in resp.json()["detail"]
