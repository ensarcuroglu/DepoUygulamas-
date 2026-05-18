"""AssistantAiService HTTP client.

BackendProje icin AssistantAiService'e (port 8006) baglanan ince proxy
istemcisi. DocAi/ExcelAi pattern'inin aynisi: INTERNAL_API_KEY ile authenticate,
JSON gonderir, JSON alir, tipli hata sinifi firlatir.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
from fastapi import status

from app.application.dto.asistan_dto import (
    AsistanUpstreamChatRequestDTO,
    AsistanUpstreamChatResponseDTO,
)
from app.core.config import Settings, get_settings
from core.api_exceptions import APIException


class AssistantAiClientError(APIException):
    """AssistantAiService entegrasyonu icin temel hata."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        super().__init__(status_code, message)


class AssistantAiClientUnavailableError(AssistantAiClientError):
    pass


class AssistantAiClientTimeoutError(AssistantAiClientError):
    pass


class AssistantAiClientUpstreamError(AssistantAiClientError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"AssistantAiService hatasi ({status_code}): {detail}", status_code)


class AssistantAiClient:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._base_url = self._settings.assistant_ai_service_url.rstrip("/")
        self._timeout = self._settings.assistant_ai_service_timeout

    # -----------------------------------------------------------------------
    # Public
    # -----------------------------------------------------------------------

    def chat(
        self,
        request: AsistanUpstreamChatRequestDTO,
    ) -> AsistanUpstreamChatResponseDTO:
        payload = self._post("/api/asistan/chat", request.model_dump(mode="json"))
        return AsistanUpstreamChatResponseDTO.model_validate(payload)

    def healthz(self) -> dict[str, Any]:
        return self._get("/healthz")

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        key = self._settings.internal_api_key
        if key:
            headers["X-Internal-Api-Key"] = key
        return headers

    def _post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", path, json_body=json_body)

    def _get(self, path: str) -> dict[str, Any]:
        return self._request("GET", path)

    def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(
                    method,
                    url,
                    json=json_body,
                    headers=self._headers(),
                )
        except httpx.ConnectError as exc:
            raise AssistantAiClientUnavailableError(
                f"AssistantAiService erisilemedi: {exc}",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        except httpx.TimeoutException as exc:
            raise AssistantAiClientTimeoutError(
                f"AssistantAiService zaman asimi: {exc}",
                status.HTTP_504_GATEWAY_TIMEOUT,
            ) from exc
        except httpx.HTTPError as exc:
            raise AssistantAiClientError(f"AssistantAiService hatasi: {exc}") from exc

        if response.status_code >= 400:
            try:
                payload = response.json()
                detail = (
                    payload.get("detail", str(payload))
                    if isinstance(payload, dict)
                    else str(payload)
                )
            except ValueError:
                detail = response.text
            raise AssistantAiClientUpstreamError(response.status_code, detail)

        try:
            return response.json()
        except ValueError as exc:
            raise AssistantAiClientError(
                "AssistantAiService gecersiz JSON dondurdu",
            ) from exc
