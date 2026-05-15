"""Faz 4 — JwtAuthClient testleri."""

from __future__ import annotations

import asyncio
import base64
import json
import time

import httpx
import pytest

from app.infrastructure.auth import JwtAuthClient, JwtAuthError


def _make_jwt(exp_offset_sec: float = 8 * 3600) -> str:
    """`exp` claim'li sahte JWT (signature doğrulanmaz)."""
    header = base64.urlsafe_b64encode(b'{"alg":"HS256"}').rstrip(b"=").decode()
    payload = {"sub": "admin", "exp": int(time.time() + exp_offset_sec)}
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    sig = base64.urlsafe_b64encode(b"sig").rstrip(b"=").decode()
    return f"{header}.{body}.{sig}"


@pytest.mark.unit
async def test_login_caches_token() -> None:
    cagri_sayisi = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal cagri_sayisi
        assert request.url.path == "/api/auth/login"
        body = json.loads(request.content)
        assert body == {"kullanici_adi": "admin", "sifre": "Admin1234!"}
        cagri_sayisi += 1
        return httpx.Response(
            200,
            json={
                "access_token": _make_jwt(),
                "refresh_token": "abc:secret",
                "token_type": "bearer",
                "user": {"id": 1, "kullanici_adi": "admin", "rol": "admin"},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://test", transport=transport
    ) as client:
        auth = JwtAuthClient(
            base_url="http://test",
            username="admin",
            password="Admin1234!",
            client=client,
        )
        t1 = await auth.get_access_token()
        t2 = await auth.get_access_token()
        # Aynı çağrılar tek login üretmeli (cache).
        assert t1 == t2
        assert cagri_sayisi == 1


@pytest.mark.unit
async def test_refresh_used_when_expired() -> None:
    cagrilar: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        cagrilar.append(request.url.path)
        if request.url.path == "/api/auth/login":
            return httpx.Response(
                200,
                json={
                    # 30 saniye sonra dolacak; refresh buffer 60 sn ile derhal refresh tetiklenir
                    "access_token": _make_jwt(exp_offset_sec=30),
                    "refresh_token": "first:secret",
                    "token_type": "bearer",
                    "user": {"id": 1, "kullanici_adi": "admin", "rol": "admin"},
                },
            )
        assert request.url.path == "/api/auth/refresh"
        return httpx.Response(
            200,
            json={
                "access_token": _make_jwt(exp_offset_sec=8 * 3600),
                "refresh_token": "second:secret",
                "token_type": "bearer",
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://test", transport=transport
    ) as client:
        auth = JwtAuthClient(
            base_url="http://test",
            username="admin",
            password="Admin1234!",
            client=client,
            refresh_buffer_sec=60,
        )
        await auth.get_access_token()  # login
        await auth.get_access_token()  # refresh tetiklenmeli
        assert cagrilar == ["/api/auth/login", "/api/auth/refresh"]


@pytest.mark.unit
async def test_login_failure_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"detail": "Geçersiz şifre"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://test", transport=transport
    ) as client:
        auth = JwtAuthClient(
            base_url="http://test",
            username="admin",
            password="yanlis",
            client=client,
        )
        with pytest.raises(JwtAuthError, match="HTTP 401"):
            await auth.get_access_token()


@pytest.mark.unit
async def test_refresh_failure_falls_back_to_login() -> None:
    state = {"step": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        state["step"] += 1
        if request.url.path == "/api/auth/refresh":
            return httpx.Response(401, json={"detail": "refresh süresi doldu"})
        # /api/auth/login
        return httpx.Response(
            200,
            json={
                "access_token": _make_jwt(exp_offset_sec=10 if state["step"] == 1 else 8 * 3600),
                "refresh_token": f"tok-{state['step']}:secret",
                "token_type": "bearer",
                "user": {"id": 1, "kullanici_adi": "admin", "rol": "admin"},
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(
        base_url="http://test", transport=transport
    ) as client:
        auth = JwtAuthClient(
            base_url="http://test",
            username="admin",
            password="x",
            client=client,
            refresh_buffer_sec=60,
        )
        await auth.get_access_token()  # ilk login (kısa ömürlü)
        # İkinci çağrı refresh dener, 401 alır, login fallback'i yapar
        await auth.get_access_token()
        # En az 1 login + 1 refresh + 1 login = 3 istek
        assert state["step"] >= 3


@pytest.mark.unit
async def test_concurrent_get_token_makes_single_login() -> None:
    """Eşzamanlı 10 caller → tek login (asyncio.Lock)."""
    cagri_sayisi = 0

    async def slow_handler(request: httpx.Request) -> httpx.Response:
        nonlocal cagri_sayisi
        cagri_sayisi += 1
        await asyncio.sleep(0.05)
        return httpx.Response(
            200,
            json={
                "access_token": _make_jwt(),
                "refresh_token": "tok:secret",
                "token_type": "bearer",
                "user": {"id": 1, "kullanici_adi": "admin", "rol": "admin"},
            },
        )

    transport = httpx.MockTransport(slow_handler)
    async with httpx.AsyncClient(
        base_url="http://test", transport=transport
    ) as client:
        auth = JwtAuthClient(
            base_url="http://test",
            username="admin",
            password="x",
            client=client,
        )
        tokens = await asyncio.gather(*[auth.get_access_token() for _ in range(10)])
        assert len(set(tokens)) == 1
        assert cagri_sayisi == 1


@pytest.mark.unit
async def test_missing_credentials_rejected() -> None:
    async with httpx.AsyncClient() as client:
        with pytest.raises(JwtAuthError, match="zorunlu"):
            JwtAuthClient(
                base_url="http://test", username="", password="", client=client
            )
