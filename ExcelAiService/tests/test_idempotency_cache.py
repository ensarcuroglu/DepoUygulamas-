"""IdempotencyCache LRU + TTL davranisi."""

from __future__ import annotations

import time

import pytest

from app.core.services.idempotency_cache import IdempotencyCache

pytestmark = pytest.mark.unit


def test_set_then_get_returns_value():
    cache = IdempotencyCache(max_entries=4, ttl_seconds=60)
    cache.set("k1", {"a": 1})
    assert cache.get("k1") == {"a": 1}


def test_missing_key_returns_none():
    cache = IdempotencyCache(max_entries=4, ttl_seconds=60)
    assert cache.get("yok") is None


def test_empty_key_is_noop():
    cache = IdempotencyCache(max_entries=4, ttl_seconds=60)
    cache.set("", "x")
    assert cache.get("") is None
    assert len(cache) == 0


def test_lru_evicts_oldest():
    cache = IdempotencyCache(max_entries=2, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("c", 3)  # 'a' atilir
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3


def test_get_refreshes_lru_order():
    cache = IdempotencyCache(max_entries=2, ttl_seconds=60)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")  # 'a' move_to_end
    cache.set("c", 3)  # 'b' atilmali
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_ttl_expiry(monkeypatch):
    cache = IdempotencyCache(max_entries=4, ttl_seconds=10)

    now = {"t": 1000.0}

    def fake_monotonic() -> float:
        return now["t"]

    monkeypatch.setattr(
        "app.core.services.idempotency_cache.time.monotonic", fake_monotonic
    )

    cache.set("a", 1)
    assert cache.get("a") == 1

    now["t"] = 1015.0  # 15 sn sonra (TTL=10)
    assert cache.get("a") is None
