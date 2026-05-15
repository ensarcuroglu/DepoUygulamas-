"""WMS Backend için JWT auth istemcisi.

Akış:
  1. `POST /api/auth/login` ile admin user üzerinden access + refresh token alır.
  2. Access token'ın `exp` claim'ini decode edip TTL hesaplar.
  3. Süre dolmadan `JWT_REFRESH_BUFFER_SEC` saniye önce `POST /api/auth/refresh`
     ile rotation yapar (eski refresh token geçersizleşir).
  4. Refresh başarısızsa tekrar login dener.

`asyncio.Lock` ile eşzamanlı refresh çağrılarında tek aktör garantilenir.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import time
from dataclasses import dataclass

import httpx

log = logging.getLogger("data-gen.auth")


class JwtAuthError(RuntimeError):
    """Login / refresh başarısız."""


@dataclass
class _TokenState:
    access_token: str
    refresh_token: str
    expires_at: float  # epoch seconds


def _decode_jwt_exp(token: str) -> float:
    """JWT payload'ından `exp` (epoch sec) çıkarır.

    Standart JWT yapısı: ``header.payload.signature``. Base64 padding eksikse
    eklenir. Decode başarısızsa `JwtAuthError` fırlatılır.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise ValueError("JWT formatı geçersiz (3 parça bekleniyor).")
        payload_b64 = parts[1]
        # base64 url-safe + padding
        padding = "=" * (-len(payload_b64) % 4)
        decoded = base64.urlsafe_b64decode(payload_b64 + padding)
        claims = json.loads(decoded)
        exp = claims.get("exp")
        if not isinstance(exp, (int, float)):
            raise ValueError("JWT payload `exp` claim'i yok.")
        return float(exp)
    except (ValueError, json.JSONDecodeError) as exc:
        raise JwtAuthError(f"JWT decode hatası: {exc}") from exc


class JwtAuthClient:
    """Backend'den access token alır + cache'ler + refresh akışı yönetir."""

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        client: httpx.AsyncClient,
        refresh_buffer_sec: int = 60,
    ) -> None:
        if not username or not password:
            raise JwtAuthError(
                "DATAGEN_ADMIN_USERNAME ve DATAGEN_ADMIN_PASSWORD zorunlu."
            )
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.client = client
        self.refresh_buffer_sec = refresh_buffer_sec
        self._state: _TokenState | None = None
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        """Geçerli access token döner. Süresi dolmuşsa refresh/login eder."""
        async with self._lock:
            if self._state is None:
                await self._login_locked()
            elif self._needs_refresh(self._state):
                try:
                    await self._refresh_locked()
                except JwtAuthError:
                    log.warning("Refresh başarısız; tekrar login deneniyor.")
                    await self._login_locked()
            assert self._state is not None
            return self._state.access_token

    async def authorization_header(self) -> dict[str, str]:
        """`Authorization: Bearer …` header'ı döner."""
        token = await self.get_access_token()
        return {"Authorization": f"Bearer {token}"}

    def _needs_refresh(self, state: _TokenState) -> bool:
        return time.time() >= (state.expires_at - self.refresh_buffer_sec)

    async def _login_locked(self) -> None:
        url = f"{self.base_url}/api/auth/login"
        body = {"kullanici_adi": self.username, "sifre": self.password}
        log.info("Login başlatılıyor: %s as %s", self.base_url, self.username)
        try:
            r = await self.client.post(url, json=body)
        except httpx.HTTPError as exc:
            raise JwtAuthError(f"Login network hatası: {exc}") from exc
        if r.status_code != 200:
            raise JwtAuthError(
                f"Login HTTP {r.status_code}: {r.text[:200]}"
            )
        payload = r.json()
        self._state = _TokenState(
            access_token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            expires_at=_decode_jwt_exp(payload["access_token"]),
        )
        log.info(
            "Login başarılı. Access token TTL: %.0f sn",
            self._state.expires_at - time.time(),
        )

    async def _refresh_locked(self) -> None:
        assert self._state is not None
        url = f"{self.base_url}/api/auth/refresh"
        body = {"refresh_token": self._state.refresh_token}
        try:
            r = await self.client.post(url, json=body)
        except httpx.HTTPError as exc:
            raise JwtAuthError(f"Refresh network hatası: {exc}") from exc
        if r.status_code != 200:
            raise JwtAuthError(
                f"Refresh HTTP {r.status_code}: {r.text[:200]}"
            )
        payload = r.json()
        self._state = _TokenState(
            access_token=payload["access_token"],
            refresh_token=payload["refresh_token"],
            expires_at=_decode_jwt_exp(payload["access_token"]),
        )
