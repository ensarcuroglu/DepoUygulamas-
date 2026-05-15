"""REST emitter — HTTPX async, Semaphore, exponential backoff, Idempotency-Key.

Tek endpoint için tasarlandı: ``RestEmitter(client, "/api/urunler/")``.
Her senaryo, ihtiyaç duyduğu endpoint başına bir emitter instance'ı kurar;
ortak `asyncio.Semaphore` ile global concurrency limiti uygulanır.

Retry politikası:
  - 5xx ve `httpx.HTTPError` → exponential backoff (0.5s × 2^n, max 3 retry)
  - 4xx → retry yok (validation/auth hatası), `failed` sayar
  - 200/201/202 → success
  - 409 + Idempotency-Key → success (idempotent re-emit; backend cache)
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
import uuid
from collections.abc import Sequence

import httpx
from pydantic import BaseModel

from app.infrastructure.auth import JwtAuthClient

from .base import EmitSummary

log = logging.getLogger("data-gen.rest")

_RETRYABLE_STATUS = {500, 502, 503, 504}


class RestEmitter:
    """`IEmitter` implementasyonu — Pydantic DTO listesini REST endpoint'e basar.

    Args:
        client: Paylaşılan `httpx.AsyncClient`.
        path: Endpoint yolu (örn. ``/api/urunler/``).
        auth: JWT auth client; her istek için Bearer header üretir.
        semaphore: Concurrency limiti (paylaşımlı; tüm emitter'lar tek havuz).
        method: HTTP method (default POST).
        max_retries: 5xx/network hatalarında tekrar sayısı.
        backoff_base: Backoff başlangıcı (saniye). Çarpan 2.0, jitter ±%20.
        idempotency: True ise her istek için UUID4 `Idempotency-Key` üretir.
    """

    def __init__(
        self,
        *,
        client: httpx.AsyncClient,
        path: str,
        auth: JwtAuthClient,
        semaphore: asyncio.Semaphore,
        method: str = "POST",
        max_retries: int = 3,
        backoff_base: float = 0.5,
        idempotency: bool = False,
        timeout: float = 30.0,
    ) -> None:
        self.client = client
        self.path = path
        self.auth = auth
        self.semaphore = semaphore
        self.method = method.upper()
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.idempotency = idempotency
        self.timeout = timeout

        self._summary = EmitSummary()
        self._last_responses: list[dict[str, object]] = []
        self._closed = False

    # ------------------------------------------------------------------
    # IEmitter
    # ------------------------------------------------------------------

    async def emit_batch(self, items: Sequence[BaseModel]) -> None:
        await self._emit_internal(items)

    async def close(self) -> None:
        # Client paylaşımlı olduğu için burada kapatmıyoruz.
        self._summary.mark_finished()
        self._closed = True

    def summary(self) -> EmitSummary:
        return self._summary

    # ------------------------------------------------------------------
    # Public extras
    # ------------------------------------------------------------------

    async def emit_batch_with_responses(
        self, items: Sequence[BaseModel]
    ) -> list[dict[str, object] | None]:
        """Batch'i basar ve sırayla response JSON'larını döner.

        Hatalı isteklerin slot'u `None` olur. Senaryo, dönen `id` alanlarını
        referans havuzlara aktarmak için bu metodu çağırır.
        """
        await self._emit_internal(items)
        return list(self._last_responses)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _emit_internal(self, items: Sequence[BaseModel]) -> None:
        if self._closed:
            raise RuntimeError("RestEmitter zaten kapalı.")
        if not items:
            self._last_responses = []
            return

        async def _one(item: BaseModel, idx: int) -> dict[str, object] | None:
            async with self.semaphore:
                return await self._send_one(item, idx)

        tasks = [_one(item, i) for i, item in enumerate(items)]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        self._last_responses = list(results)  # type: ignore[arg-type]

    async def _send_one(
        self, item: BaseModel, idx: int
    ) -> dict[str, object] | None:
        payload = item.model_dump(mode="json")
        headers = await self.auth.authorization_header()
        if self.idempotency:
            headers["Idempotency-Key"] = str(uuid.uuid4())

        attempt = 0
        t0 = time.perf_counter()
        while True:
            try:
                resp = await self.client.request(
                    self.method,
                    self.path,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
            except httpx.HTTPError as exc:
                if attempt >= self.max_retries:
                    return self._record_failure(
                        t0, f"network: {type(exc).__name__}: {exc}"
                    )
                await self._sleep_backoff(attempt)
                attempt += 1
                continue

            if resp.status_code in {200, 201, 202}:
                return self._record_success(t0, resp)

            if resp.status_code == 409 and self.idempotency:
                # Idempotent re-emit — backend cached yanıtı döndürür.
                return self._record_success(t0, resp)

            if resp.status_code in _RETRYABLE_STATUS and attempt < self.max_retries:
                await self._sleep_backoff(attempt)
                attempt += 1
                continue

            # 4xx ya da tükenmiş retry — kalıcı başarısızlık.
            return self._record_failure(
                t0, f"HTTP {resp.status_code}: {resp.text[:200]}"
            )

    def _record_success(
        self, t0: float, resp: httpx.Response
    ) -> dict[str, object] | None:
        self._summary.total += 1
        self._summary.success += 1
        self._summary.latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        try:
            return resp.json()
        except ValueError:
            return None

    def _record_failure(self, t0: float, err: str) -> None:
        self._summary.total += 1
        self._summary.failed += 1
        self._summary.errors.append(err)
        self._summary.latencies_ms.append((time.perf_counter() - t0) * 1000.0)
        log.warning("REST emit fail %s %s: %s", self.method, self.path, err)
        return None

    async def _sleep_backoff(self, attempt: int) -> None:
        # 0.5 → 1 → 2 → 4 (jitter ±%20)
        base = self.backoff_base * (2 ** attempt)
        jitter = base * random.uniform(-0.2, 0.2)
        await asyncio.sleep(max(0.0, base + jitter))
