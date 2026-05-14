"""ExcelAiService HTTP client.

BackendProje icin ExcelAiService'e (port 8004) baglanan ince proxy
istemcisi. DocAiClient pattern'inin aynisi: INTERNAL_API_KEY ile
authenticate, dosyayi multipart olarak iletir, JSON cevabini dondurur.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
from fastapi import status

from app.core.config import Settings, get_settings
from core.api_exceptions import APIException


class ExcelAiClientError(APIException):
    """ExcelAiService entegrasyonu icin temel hata."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        super().__init__(status_code, message)


class ExcelAiClientUnavailableError(ExcelAiClientError):
    pass


class ExcelAiClientTimeoutError(ExcelAiClientError):
    pass


class ExcelAiClientUpstreamError(ExcelAiClientError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"ExcelAiService hatasi ({status_code}): {detail}", status_code)


class ExcelAiClient:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._base_url = self._settings.excel_ai_service_url.rstrip("/")
        self._timeout = self._settings.excel_ai_service_timeout

    def hedef_semalar(self) -> dict[str, Any]:
        return self._get("/api/excel/hedef-semalar")

    def yorumla(
        self,
        *,
        filename: str,
        content_type: Optional[str],
        content: bytes,
        soru: Optional[str] = None,
        sheet_name: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        data: dict[str, str] = {}
        if soru:
            data["soru"] = soru
        if sheet_name:
            data["sheet_name"] = sheet_name
        return self._post_multipart(
            "/api/excel/yorumla",
            filename=filename,
            content_type=content_type,
            content=content,
            data=data,
            idempotency_key=idempotency_key,
        )

    def sema_esle(
        self,
        *,
        filename: str,
        content_type: Optional[str],
        content: bytes,
        hedef_sema: str,
        sheet_name: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        data: dict[str, str] = {"hedef_sema": hedef_sema}
        if sheet_name:
            data["sheet_name"] = sheet_name
        return self._post_multipart(
            "/api/excel/sema-esle",
            filename=filename,
            content_type=content_type,
            content=content,
            data=data,
            idempotency_key=idempotency_key,
        )

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _auth_headers(self, *, idempotency_key: Optional[str] = None) -> dict[str, str]:
        api_key = self._settings.internal_api_key
        if not api_key:
            raise ExcelAiClientUnavailableError(
                "INTERNAL_API_KEY yapilandirilmamis.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        headers = {"X-Internal-Api-Key": api_key}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        return headers

    def _get(self, path: str) -> dict[str, Any]:
        headers = self._auth_headers()
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(f"{self._base_url}{path}", headers=headers)
        except httpx.TimeoutException as exc:
            raise ExcelAiClientTimeoutError(
                "ExcelAiService zaman asimina ugradi.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            ) from exc
        except httpx.HTTPError as exc:
            raise ExcelAiClientUnavailableError(
                "ExcelAiService'e ulasilamiyor.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        return self._parse(response)

    def _post_multipart(
        self,
        path: str,
        *,
        filename: str,
        content_type: Optional[str],
        content: bytes,
        data: dict[str, str],
        idempotency_key: Optional[str] = None,
    ) -> dict[str, Any]:
        headers = self._auth_headers(idempotency_key=idempotency_key)
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
                    f"{self._base_url}{path}",
                    files=files,
                    data=data,
                    headers=headers,
                )
        except httpx.TimeoutException as exc:
            raise ExcelAiClientTimeoutError(
                "ExcelAiService zaman asimina ugradi.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            ) from exc
        except httpx.HTTPError as exc:
            raise ExcelAiClientUnavailableError(
                "ExcelAiService'e ulasilamiyor.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= status.HTTP_400_BAD_REQUEST:
            detail = self._response_detail(response)
            raise ExcelAiClientUpstreamError(response.status_code, detail)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ExcelAiClientError("ExcelAiService gecersiz JSON dondu.") from exc
        if not isinstance(payload, dict):
            raise ExcelAiClientError("ExcelAiService beklenmeyen yanit formati dondu.")
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
