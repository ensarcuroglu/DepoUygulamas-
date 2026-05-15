"""Faz 5 — `task_load` senaryo testleri (rabbit + rest modu)."""

from __future__ import annotations

import base64
import itertools
import json
import time
from collections import Counter

import httpx
import pytest

from app.core.config import Settings
from app.infrastructure.emitters import InMemoryRabbitPublisher
from app.scenarios import TaskLoadParams, run_task_load


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


# ---------------------------------------------------------------------------
# target='rabbit'
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_task_load_rabbit_publishes_count_messages() -> None:
    publisher = InMemoryRabbitPublisher()
    params = TaskLoadParams(count=200, seed=42, target="rabbit", batch_size=50)
    settings = Settings(BACKEND_BASE_URL="http://test")

    result = await run_task_load(params, settings=settings, publisher=publisher)

    assert result.total == 200
    assert result.success == 200
    assert result.failed == 0
    assert len(publisher.published) == 200

    # Routing key dağılımı PerformansEventTipi'ye uyar
    rk_suffixes = Counter(
        rk.split(".")[-1] for rk, _ in publisher.published
    )
    assert set(rk_suffixes.keys()) <= {
        "GOREV_BASLATILDI", "GOREV_TAMAMLANDI", "GOREV_IPTAL"
    }


@pytest.mark.unit
async def test_task_load_rabbit_dlq_simulation() -> None:
    """fail_routing_keys ile bir tipin 'unroutable' simülasyonu — DLQ semantiği."""
    publisher = InMemoryRabbitPublisher(
        fail_routing_keys={"lms.gorev_performans.GOREV_IPTAL"}
    )
    params = TaskLoadParams(count=300, seed=42, target="rabbit", batch_size=100)
    settings = Settings(BACKEND_BASE_URL="http://test")

    result = await run_task_load(params, settings=settings, publisher=publisher)

    # %15 dağılım → ~45 fail, ±toleransla
    assert 30 <= result.failed <= 60
    assert result.success == 300 - result.failed


@pytest.mark.unit
async def test_task_load_rabbit_rejects_client_param() -> None:
    publisher = InMemoryRabbitPublisher()
    params = TaskLoadParams(count=5, target="rabbit")
    settings = Settings(BACKEND_BASE_URL="http://test")
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="target='rabbit'"):
            await run_task_load(
                params, settings=settings, publisher=publisher, client=client
            )


# ---------------------------------------------------------------------------
# target='rest'
# ---------------------------------------------------------------------------


@pytest.mark.unit
async def test_task_load_rest_hits_uret_endpoint() -> None:
    id_seq = itertools.count(1)
    cagrilar: Counter[str] = Counter()
    idempotency_keys: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        cagrilar[request.url.path] += 1
        if request.url.path == "/api/auth/login":
            return _login_response()
        # idempotency-key header ölç
        key = request.headers.get("Idempotency-Key", "")
        if key:
            idempotency_keys.append(key)
        return httpx.Response(201, json=[{"id": next(id_seq)}])

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        params = TaskLoadParams(count=50, seed=42, target="rest", batch_size=25)
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="x",
        )
        result = await run_task_load(params, settings=settings, client=client)
    finally:
        await client.aclose()

    assert cagrilar["/api/v1/toplama-gorevleri/uret"] == 50
    assert result.success == 50
    assert result.failed == 0
    # Idempotency-Key destekli endpoint — her istekte benzersiz UUID
    assert len(idempotency_keys) == 50
    assert len(set(idempotency_keys)) == 50


@pytest.mark.unit
async def test_task_load_rest_rejects_publisher_param() -> None:
    params = TaskLoadParams(count=5, target="rest")
    settings = Settings(
        BACKEND_BASE_URL="http://test",
        DATAGEN_ADMIN_USERNAME="admin",
        DATAGEN_ADMIN_PASSWORD="x",
    )
    publisher = InMemoryRabbitPublisher()
    async with httpx.AsyncClient() as client:
        with pytest.raises(ValueError, match="target='rest'"):
            await run_task_load(
                params, settings=settings, publisher=publisher, client=client
            )


# ---------------------------------------------------------------------------
# Params validation
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_task_load_params_validates_count_positive() -> None:
    with pytest.raises(ValueError, match="count"):
        TaskLoadParams(count=0, target="rest")


@pytest.mark.unit
def test_task_load_params_validates_target_via_matrix() -> None:
    # target='file' izinsiz → matriste reddedilir
    with pytest.raises(Exception):
        TaskLoadParams(count=1, target="file")  # type: ignore[arg-type]
