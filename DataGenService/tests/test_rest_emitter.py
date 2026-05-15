"""Faz 4 — RestEmitter testleri (HTTPX MockTransport)."""

from __future__ import annotations

import asyncio
import base64
import itertools
import json
import time

import httpx
import pytest
from pydantic import BaseModel

from app.infrastructure.auth import JwtAuthClient
from app.infrastructure.emitters import RestEmitter


class _SampleDTO(BaseModel):
    isim: str
    sayi: int


def _make_jwt(exp_offset_sec: float = 8 * 3600) -> str:
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = {"sub": "admin", "exp": int(time.time() + exp_offset_sec)}
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


@pytest.fixture()
async def auth_client_factory():
    """Test'in handler callback'i ile MockTransport client + auth üretir."""

    async def _factory(handler):
        client = httpx.AsyncClient(
            base_url="http://test", transport=httpx.MockTransport(handler)
        )
        auth = JwtAuthClient(
            base_url="http://test",
            username="admin",
            password="x",
            client=client,
        )
        return client, auth

    return _factory


@pytest.mark.unit
async def test_rest_emitter_happy_path(auth_client_factory) -> None:
    response_counter = itertools.count(1)

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        assert request.url.path == "/api/test/"
        assert request.headers["Authorization"].startswith("Bearer ")
        return httpx.Response(201, json={"id": next(response_counter), "ok": True})

    client, auth = await auth_client_factory(handler)
    try:
        sem = asyncio.Semaphore(5)
        emitter = RestEmitter(
            client=client, path="/api/test/", auth=auth, semaphore=sem
        )
        items = [_SampleDTO(isim=f"x{i}", sayi=i) for i in range(5)]
        responses = await emitter.emit_batch_with_responses(items)
        assert [r["id"] for r in responses] == [1, 2, 3, 4, 5]  # type: ignore[index]
        summary = emitter.summary()
        assert summary.success == 5
        assert summary.failed == 0
        assert summary.total == 5
    finally:
        await client.aclose()


@pytest.mark.unit
async def test_rest_emitter_retries_5xx(auth_client_factory) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        call_count["n"] += 1
        if call_count["n"] < 3:
            return httpx.Response(503, json={"detail": "geçici"})
        return httpx.Response(201, json={"id": 42})

    client, auth = await auth_client_factory(handler)
    try:
        emitter = RestEmitter(
            client=client,
            path="/api/test/",
            auth=auth,
            semaphore=asyncio.Semaphore(1),
            backoff_base=0.001,  # test hızlı koşsun
            max_retries=3,
        )
        responses = await emitter.emit_batch_with_responses([_SampleDTO(isim="x", sayi=1)])
        assert responses[0] == {"id": 42}
        assert emitter.summary().success == 1
        assert call_count["n"] == 3
    finally:
        await client.aclose()


@pytest.mark.unit
async def test_rest_emitter_4xx_not_retried(auth_client_factory) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        call_count["n"] += 1
        return httpx.Response(422, json={"detail": "validation"})

    client, auth = await auth_client_factory(handler)
    try:
        emitter = RestEmitter(
            client=client,
            path="/api/test/",
            auth=auth,
            semaphore=asyncio.Semaphore(1),
            backoff_base=0.001,
            max_retries=3,
        )
        responses = await emitter.emit_batch_with_responses([_SampleDTO(isim="x", sayi=1)])
        assert responses[0] is None
        assert emitter.summary().failed == 1
        # 4xx → tek deneme
        assert call_count["n"] == 1
    finally:
        await client.aclose()


@pytest.mark.unit
async def test_rest_emitter_retries_exhausted(auth_client_factory) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        return httpx.Response(503)

    client, auth = await auth_client_factory(handler)
    try:
        emitter = RestEmitter(
            client=client,
            path="/api/test/",
            auth=auth,
            semaphore=asyncio.Semaphore(1),
            backoff_base=0.001,
            max_retries=2,
        )
        responses = await emitter.emit_batch_with_responses([_SampleDTO(isim="x", sayi=1)])
        assert responses[0] is None
        assert emitter.summary().failed == 1
        assert emitter.summary().errors  # hata mesajı kaydedildi
    finally:
        await client.aclose()


@pytest.mark.unit
async def test_rest_emitter_idempotency_key_header(auth_client_factory) -> None:
    captured: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        captured.append(request.headers.get("Idempotency-Key", ""))
        return httpx.Response(201, json={"id": 1})

    client, auth = await auth_client_factory(handler)
    try:
        emitter = RestEmitter(
            client=client,
            path="/api/test/",
            auth=auth,
            semaphore=asyncio.Semaphore(2),
            idempotency=True,
        )
        await emitter.emit_batch_with_responses(
            [_SampleDTO(isim="a", sayi=1), _SampleDTO(isim="b", sayi=2)]
        )
        # İki istek → iki farklı UUID
        assert len(captured) == 2
        assert all(captured), "Idempotency-Key her istekte gönderilmeli"
        assert captured[0] != captured[1], "UUID'ler benzersiz olmalı"
    finally:
        await client.aclose()


@pytest.mark.unit
async def test_rest_emitter_concurrency_limit_respected(auth_client_factory) -> None:
    """Semaphore(N) ile aynı anda > N istek olamaz."""
    inflight = {"current": 0, "max_seen": 0}

    async def handler_async(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        inflight["current"] += 1
        inflight["max_seen"] = max(inflight["max_seen"], inflight["current"])
        await asyncio.sleep(0.02)
        inflight["current"] -= 1
        return httpx.Response(201, json={"id": 1})

    client = httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(handler_async),  # type: ignore[arg-type]
    )
    try:
        auth = JwtAuthClient(
            base_url="http://test",
            username="admin",
            password="x",
            client=client,
        )
        emitter = RestEmitter(
            client=client,
            path="/api/test/",
            auth=auth,
            semaphore=asyncio.Semaphore(3),
        )
        items = [_SampleDTO(isim=f"x{i}", sayi=i) for i in range(15)]
        await emitter.emit_batch(items)
        assert inflight["max_seen"] <= 3, (
            f"Concurrency limiti aşıldı: max_seen={inflight['max_seen']}"
        )
    finally:
        await client.aclose()


@pytest.mark.unit
async def test_rest_emitter_empty_batch_is_noop(auth_client_factory) -> None:
    handler_called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        handler_called["n"] += 1
        if request.url.path == "/api/auth/login":
            return _login_response()
        return httpx.Response(201, json={"id": 1})

    client, auth = await auth_client_factory(handler)
    try:
        emitter = RestEmitter(
            client=client, path="/api/test/", auth=auth, semaphore=asyncio.Semaphore(1)
        )
        await emitter.emit_batch([])
        # Login bile yapılmamalı; istek hiç gitmedi.
        assert handler_called["n"] == 0
        assert emitter.summary().total == 0
    finally:
        await client.aclose()


@pytest.mark.unit
async def test_rest_emitter_409_with_idempotency_treated_as_success(
    auth_client_factory,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        return httpx.Response(409, json={"detail": "duplicate, cached"})

    client, auth = await auth_client_factory(handler)
    try:
        emitter = RestEmitter(
            client=client,
            path="/api/test/",
            auth=auth,
            semaphore=asyncio.Semaphore(1),
            idempotency=True,
        )
        await emitter.emit_batch([_SampleDTO(isim="x", sayi=1)])
        assert emitter.summary().success == 1
        assert emitter.summary().failed == 0
    finally:
        await client.aclose()
