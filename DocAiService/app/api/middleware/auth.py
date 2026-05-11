"""Internal service authentication middleware."""

from __future__ import annotations

import hmac
import logging
from collections.abc import Callable

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.config import Settings, get_settings

log = logging.getLogger(__name__)


SettingsProvider = Callable[[], Settings]


class InternalApiKeyMiddleware:
    """Require X-Internal-Api-Key for every HTTP request except CORS preflight."""

    def __init__(
        self,
        app: ASGIApp,
        settings_provider: SettingsProvider = get_settings,
    ) -> None:
        self.app = app
        self.settings_provider = settings_provider

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        if scope.get("method", "").upper() == "OPTIONS":
            await self.app(scope, receive, send)
            return

        settings = self.settings_provider()
        expected = settings.internal_api_key
        provided = self._header_value(scope, b"x-internal-api-key")

        if not expected:
            log.warning("INTERNAL_API_KEY is not configured; internal endpoints disabled")
            await self._reject(scope, receive, send, "Internal API kimligi yapilandirilmamis")
            return

        if not provided or not hmac.compare_digest(provided, expected):
            await self._reject(scope, receive, send, "Internal API kimligi eksik veya gecersiz")
            return

        await self.app(scope, receive, send)

    @staticmethod
    def _header_value(scope: Scope, header_name: bytes) -> str | None:
        for name, value in scope.get("headers", []):
            if name.lower() == header_name:
                return value.decode("utf-8")
        return None

    @staticmethod
    async def _reject(
        scope: Scope,
        receive: Receive,
        send: Send,
        detail: str,
    ) -> None:
        response = JSONResponse(status_code=503, content={"detail": detail})
        await response(scope, receive, send)
