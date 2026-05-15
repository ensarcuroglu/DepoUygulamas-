"""Faz 4 — `seed_baseline` end-to-end orkestrasyon testi (HTTPX mock)."""

from __future__ import annotations

import base64
import itertools
import json
import time
from collections import Counter

import httpx
import pytest

from app.core.config import Settings
from app.scenarios import SeedBaselineParams, run_seed_baseline


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
async def test_seed_baseline_orchestrates_correct_endpoints() -> None:
    """raf → ürün → lot → palet sırası gözlemlenir, ID akışı çalışır."""
    id_seq = itertools.count(1)
    cagrilar: Counter[str] = Counter()

    def handler(request: httpx.Request) -> httpx.Response:
        cagrilar[request.url.path] += 1
        if request.url.path == "/api/auth/login":
            return _login_response()
        # Tüm CRUD uçları artan id döner
        return httpx.Response(201, json={"id": next(id_seq), "ok": True})

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="Admin1234!",
        )
        params = SeedBaselineParams(
            urun_count=5,
            raf_count=3,
            lot_count=4,
            palet_count=6,
            seed=42,
            concurrency=4,
            batch_size=10,
        )
        result = await run_seed_baseline(params, settings=settings, client=client)
    finally:
        await client.aclose()

    # Tüm endpoint'ler çağrıldı.
    assert cagrilar["/api/auth/login"] == 1
    assert cagrilar["/api/raflar/"] == 3
    assert cagrilar["/api/urunler/"] == 5
    assert cagrilar["/api/lotlar/"] == 4
    assert cagrilar["/api/paletler/"] == 6

    # Sonuç özetinde toplam doğru.
    assert result.total == 3 + 5 + 4 + 6
    assert result.success == 3 + 5 + 4 + 6
    assert result.failed == 0
    assert result.scenario == "seed_baseline"
    assert result.output_path is None


@pytest.mark.unit
async def test_seed_baseline_aborts_when_urunler_fail() -> None:
    """Ürün aşamasında %100 hata → palet/lot aşaması çağrılmaz."""

    cagrilar: Counter[str] = Counter()

    def handler(request: httpx.Request) -> httpx.Response:
        cagrilar[request.url.path] += 1
        if request.url.path == "/api/auth/login":
            return _login_response()
        if request.url.path == "/api/urunler/":
            return httpx.Response(422, json={"detail": "kasıtlı fail"})
        if request.url.path == "/api/raflar/":
            return httpx.Response(201, json={"id": 1})
        # /api/lotlar/, /api/paletler/ → buraya gelmemeli
        raise AssertionError(f"Beklenmedik endpoint çağrıldı: {request.url.path}")

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="x",
        )
        params = SeedBaselineParams(
            urun_count=3, raf_count=1, lot_count=2, palet_count=2,
            seed=1, concurrency=2, batch_size=5,
        )
        with pytest.raises(RuntimeError, match="Hiç ürün eklenmedi"):
            await run_seed_baseline(params, settings=settings, client=client)
    finally:
        await client.aclose()

    # raflar + ürünler çağrıldı, lot/palet asla çağrılmadı (handler'da assert).
    assert cagrilar["/api/raflar/"] == 1
    assert cagrilar["/api/urunler/"] == 3
    assert "/api/lotlar/" not in cagrilar
    assert "/api/paletler/" not in cagrilar


@pytest.mark.unit
async def test_seed_baseline_partial_failure_continues() -> None:
    """Bazı ürün isteği fail olsa bile sonraki aşamalar başarılı ID'lerle devam etmeli."""
    id_seq = itertools.count(1)
    counts = {"urun": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/auth/login":
            return _login_response()
        if request.url.path == "/api/urunler/":
            counts["urun"] += 1
            # 5'in 2'si hata
            if counts["urun"] % 3 == 0:
                return httpx.Response(422, json={"detail": "duplicate barkod"})
        return httpx.Response(201, json={"id": next(id_seq)})

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    try:
        settings = Settings(
            BACKEND_BASE_URL="http://test",
            DATAGEN_ADMIN_USERNAME="admin",
            DATAGEN_ADMIN_PASSWORD="x",
        )
        params = SeedBaselineParams(
            urun_count=6, raf_count=2, lot_count=3, palet_count=4,
            seed=1, concurrency=4, batch_size=10,
        )
        result = await run_seed_baseline(params, settings=settings, client=client)
    finally:
        await client.aclose()

    # Toplam = 2 + 6 + 3 + 4 = 15
    assert result.total == 15
    # 2 ürün isteği fail oldu → failed = 2
    assert result.failed == 2
    assert result.success == 13
