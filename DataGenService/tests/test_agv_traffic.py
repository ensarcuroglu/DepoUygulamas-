"""Faz 6 — `agv_traffic` senaryo testleri (HTTPX mock)."""

from __future__ import annotations

import base64
import itertools
import json
import time
from collections import Counter

import httpx
import pytest

from app.core.config import Settings
from app.scenarios import (
    AgvTrafficParams,
    TargetNotAllowedError,
    run_agv_traffic,
)


def _make_jwt() -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = {"sub": "admin", "exp": int(time.time() + 8 * 3600)}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.sig"


def _login_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "access_token": _make_jwt(),
            "refresh_token": "r:s",
            "token_type": "bearer",
            "user": {"id": 1, "kullanici_adi": "admin", "rol": "admin"},
        },
    )


@pytest.mark.unit
async def test_agv_traffic_hits_only_yerlestirme_endpoint() -> None:
    """Backend yerleştirme uçuna basar; AgvSim'e (port 8002) hiç istek yok."""
    cagrilar: Counter[str] = Counter()
    id_seq = itertools.count(1)
    yerlestirme_payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        cagrilar[request.url.path] += 1
        # AgvSim portu kontrolü — host'ta 8002 görmemeliyiz
        assert request.url.port != 8002, (
            "DataGenService AgvSim'e (port 8002) doğrudan çağrı yapmamalı!"
        )
        if request.url.path == "/api/auth/login":
            return _login_response()
        assert request.url.path == "/api/yerlestirme-gorevleri/"
        yerlestirme_payloads.append(json.loads(request.content))
        return httpx.Response(201, json={"id": next(id_seq), "tip": "yerlestirme"})

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        params = AgvTrafficParams(
            count=20, seed=42, palet_id_max=50, raf_id_max=20, batch_size=10
        )
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="x",
        )
        result = await run_agv_traffic(params, settings=settings, client=client)
    finally:
        await client.aclose()

    assert result.scenario == "agv_traffic"
    assert result.total == 20
    assert result.success == 20
    assert result.failed == 0
    assert cagrilar == {
        "/api/auth/login": 1,
        "/api/yerlestirme-gorevleri/": 20,
    }


@pytest.mark.unit
async def test_agv_traffic_payload_uses_id_range() -> None:
    payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        payloads.append(json.loads(request.content))
        return httpx.Response(201, json={"id": 1})

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        params = AgvTrafficParams(
            count=100,
            seed=7,
            palet_id_min=5,
            palet_id_max=15,
            raf_id_min=100,
            raf_id_max=110,
            batch_size=50,
        )
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="x",
        )
        await run_agv_traffic(params, settings=settings, client=client)
    finally:
        await client.aclose()

    assert len(payloads) == 100
    for p in payloads:
        assert 5 <= p["palet_id"] <= 15
        assert 100 <= p["onerilen_raf_id"] <= 110
        assert p["oncelik"] in (1, 3, 5)
        assert p["tip"] == "yerlestirme"


@pytest.mark.unit
async def test_agv_traffic_oncelik_dagilimi_yaklasik_dogru() -> None:
    """20% acil / 60% normal / 20% düşük — büyük örneklemde tutarlı."""
    payloads: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        payloads.append(json.loads(request.content))
        return httpx.Response(201, json={"id": 1})

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        params = AgvTrafficParams(count=1_000, seed=42, batch_size=200)
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="x",
        )
        await run_agv_traffic(params, settings=settings, client=client)
    finally:
        await client.aclose()

    sayim = Counter(p["oncelik"] for p in payloads)
    # ±%5 tolerans
    assert 150 <= sayim[1] <= 250, f"acil dağılım dışı: {sayim}"
    assert 550 <= sayim[3] <= 650, f"normal dağılım dışı: {sayim}"
    assert 150 <= sayim[5] <= 250, f"düşük dağılım dışı: {sayim}"


@pytest.mark.unit
async def test_agv_traffic_no_agvsim_call_even_on_failure() -> None:
    """Backend tüm istekleri 422 ile reddetse bile AgvSim'e çağrı olmaz."""
    cagrilar: Counter[str] = Counter()

    def handler(request: httpx.Request) -> httpx.Response:
        cagrilar[request.url.path] += 1
        # AgvSim portuna geçit yok
        assert "agv-callbacks" not in request.url.path
        assert request.url.port != 8002
        if request.url.path == "/api/auth/login":
            return _login_response()
        return httpx.Response(422, json={"detail": "kasıtlı fail"})

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        params = AgvTrafficParams(count=10, batch_size=5)
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="x",
        )
        result = await run_agv_traffic(params, settings=settings, client=client)
    finally:
        await client.aclose()

    assert result.failed == 10
    assert result.success == 0
    # Sadece login + 10 görev = 11 istek
    assert cagrilar["/api/auth/login"] == 1
    assert cagrilar["/api/yerlestirme-gorevleri/"] == 10
    # Beklenmedik bir endpoint çağrılmadı
    assert set(cagrilar.keys()) == {
        "/api/auth/login",
        "/api/yerlestirme-gorevleri/",
    }


# ---------------------------------------------------------------------------
# Params validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_agv_traffic_params_rejects_non_rest_target() -> None:
    for bad in ("rabbit", "file"):
        with pytest.raises(TargetNotAllowedError):
            AgvTrafficParams(count=1, target=bad)  # type: ignore[arg-type]


@pytest.mark.unit
def test_agv_traffic_params_validates_id_ranges() -> None:
    with pytest.raises(ValueError, match="palet_id"):
        AgvTrafficParams(count=1, palet_id_min=10, palet_id_max=5)
    with pytest.raises(ValueError, match="palet_id"):
        AgvTrafficParams(count=1, palet_id_min=0)
    with pytest.raises(ValueError, match="raf_id"):
        AgvTrafficParams(count=1, raf_id_min=10, raf_id_max=5)


@pytest.mark.unit
def test_agv_traffic_params_validates_counts() -> None:
    with pytest.raises(ValueError, match="count"):
        AgvTrafficParams(count=0)
    with pytest.raises(ValueError, match="batch_size"):
        AgvTrafficParams(count=1, batch_size=0)
    with pytest.raises(ValueError, match="concurrency"):
        AgvTrafficParams(count=1, concurrency=0)
