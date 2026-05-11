"""DocAiService HTTP client."""

from __future__ import annotations

from typing import Any, Optional

import httpx
from fastapi import status

from app.core.config import Settings, get_settings
from core.api_exceptions import APIException


class DocAiClientError(APIException):
    """Base error for DocAiService integration failures."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        super().__init__(status_code, message)


class DocAiClientUnavailableError(DocAiClientError):
    pass


class DocAiClientTimeoutError(DocAiClientError):
    pass


class DocAiClientUpstreamError(DocAiClientError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"DocAiService hatasi ({status_code}): {detail}", status_code)


class DocAiClient:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._base_url = self._settings.doc_ai_service_url.rstrip("/")
        self._timeout = self._settings.doc_ai_service_timeout

    def extract_irsaliye(
        self,
        *,
        filename: str,
        content_type: Optional[str],
        content: bytes,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        api_key = self._settings.internal_api_key
        if not api_key:
            raise DocAiClientUnavailableError(
                "INTERNAL_API_KEY yapilandirilmamis.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        headers = {"X-Internal-Api-Key": api_key}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        files = {
            "file": (
                filename,
                content,
                content_type or "application/octet-stream",
            )
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(
                    f"{self._base_url}/api/extract/irsaliye",
                    files=files,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise DocAiClientTimeoutError(
                "DocAiService zaman asimina ugradi.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            ) from exc
        except httpx.HTTPError as exc:
            raise DocAiClientUnavailableError(
                "DocAiService'e ulasilamiyor.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc

        if response.status_code >= status.HTTP_400_BAD_REQUEST:
            detail = self._response_detail(response)
            raise DocAiClientUpstreamError(response.status_code, detail)

        try:
            payload = response.json()
        except ValueError as exc:
            raise DocAiClientError("DocAiService gecersiz JSON dondu.") from exc
        if not isinstance(payload, dict):
            raise DocAiClientError("DocAiService beklenmeyen yanit formati dondu.")
        return payload

    @staticmethod
    def _response_detail(response: httpx.Response) -> str:
        try:
            payload = response.json()
        except ValueError:
            return response.text[:500]
        if isinstance(payload, dict):
            detail = payload.get("detail")
            return str(detail if detail is not None else payload)
        return str(payload)
