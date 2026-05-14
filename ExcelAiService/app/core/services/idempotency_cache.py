"""In-memory LRU + TTL idempotency cache.

`Idempotency-Key`'e gore cevap tekrar verilir. Tek surec, tek instance
icindir; HA gerekirse ileride Redis'e tasinabilir.
"""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any


class IdempotencyCache:
    def __init__(self, *, max_entries: int, ttl_seconds: int) -> None:
        self._max_entries = max(1, max_entries)
        self._ttl = max(1, ttl_seconds)
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        if not key:
            return None
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            ts, value = entry
            if now - ts > self._ttl:
                self._store.pop(key, None)
                return None
            self._store.move_to_end(key)
            return value

    def set(self, key: str, value: Any) -> None:
        if not key:
            return
        now = time.monotonic()
        with self._lock:
            self._store[key] = (now, value)
            self._store.move_to_end(key)
            while len(self._store) > self._max_entries:
                self._store.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)
