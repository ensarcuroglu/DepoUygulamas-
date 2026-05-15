"""DataGenClient unit testleri."""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from app.infrastructure.services.data_gen_client import (
    DataGenClient,
    DataGenClientTimeoutError,
    DataGenClientUnavailableError,
    DataGenClientUpstreamError,
)

pytestmark = pytest.mark.unit


def _settings(**overrides):
    base = dict(
        data_gen_service_url="http://data-gen.test",
        data_gen_service_timeout=5.0,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _patch_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    original_init = httpx.Client.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", patched_init)


def test_healthz_returns_dict(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"status": "ok", "service": "data-gen"})

    _patch_transport(monkeypatch, handler)
    client = DataGenClient(_settings())

    result = client.healthz()

    assert result == {"status": "ok", "service": "data-gen"}
    assert captured["url"] == "http://data-gen.test/healthz"


def test_run_scenario_posts_payload(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={
                "scenario": "timeseries_history",
                "total": 60,
                "success": 60,
                "failed": 0,
            },
        )

    _patch_transport(monkeypatch, handler)
    client = DataGenClient(_settings())

    result = client.run_scenario(
        "timeseries_history",
        {"count": 2, "seed": 11, "target": "file"},
    )

    assert result["scenario"] == "timeseries_history"
    assert captured["url"] == "http://data-gen.test/scenarios/timeseries_history/run"
    assert b'"count":2' in captured["body"]
    assert b'"target":"file"' in captured["body"]


def test_upstream_error_propagates_status_and_detail(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "target izinli degil"})

    _patch_transport(monkeypatch, handler)
    client = DataGenClient(_settings())

    with pytest.raises(DataGenClientUpstreamError) as ei:
        client.run_scenario("agv_traffic", {"target": "file"})

    assert ei.value.status_code == 422
    assert "target izinli degil" in ei.value.message


def test_timeout_raises_504(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("slow", request=request)

    _patch_transport(monkeypatch, handler)
    client = DataGenClient(_settings())

    with pytest.raises(DataGenClientTimeoutError) as ei:
        client.healthz()

    assert ei.value.status_code == 504


def test_connection_error_raises_503(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    _patch_transport(monkeypatch, handler)
    client = DataGenClient(_settings())

    with pytest.raises(DataGenClientUnavailableError) as ei:
        client.healthz()

    assert ei.value.status_code == 503
