"""DataGenService HTTP client.

BackendProje icin DataGenService'e (port 8005) baglanan ince proxy
istemcisi. Frontend dogrudan DataGenService'e gitmez; mevcut JWT/admin
kontrolu BackendProje router'inda kalir.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
from fastapi import status

from app.core.config import Settings, get_settings
from core.api_exceptions import APIException


class DataGenClientError(APIException):
    """DataGenService entegrasyonu icin temel hata."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
    ):
        super().__init__(status_code, message)


class DataGenClientUnavailableError(DataGenClientError):
    pass


class DataGenClientTimeoutError(DataGenClientError):
    pass


class DataGenClientUpstreamError(DataGenClientError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(f"DataGenService hatasi ({status_code}): {detail}", status_code)


class DataGenClient:
    def __init__(self, settings: Optional[Settings] = None):
        self._settings = settings or get_settings()
        self._base_url = self._settings.data_gen_service_url.rstrip("/")
        self._timeout = self._settings.data_gen_service_timeout

    def healthz(self) -> dict[str, Any]:
        return self._get("/healthz")

    def run_scenario(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post(f"/scenarios/{name}/run", payload)

    def _get(self, path: str) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(f"{self._base_url}{path}")
        except httpx.TimeoutException as exc:
            raise DataGenClientTimeoutError(
                "DataGenService zaman asimina ugradi.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            ) from exc
        except httpx.HTTPError as exc:
            raise DataGenClientUnavailableError(
                "DataGenService'e ulasilamiyor.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        return self._parse(response)

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(f"{self._base_url}{path}", json=payload)
        except httpx.TimeoutException as exc:
            raise DataGenClientTimeoutError(
                "DataGenService zaman asimina ugradi.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            ) from exc
        except httpx.HTTPError as exc:
            raise DataGenClientUnavailableError(
                "DataGenService'e ulasilamiyor.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from exc
        return self._parse(response)

    def _parse(self, response: httpx.Response) -> dict[str, Any]:
        if response.status_code >= status.HTTP_400_BAD_REQUEST:
            detail = self._response_detail(response)
            raise DataGenClientUpstreamError(response.status_code, detail)
        try:
            payload = response.json()
        except ValueError as exc:
            raise DataGenClientError("DataGenService gecersiz JSON dondu.") from exc
        if not isinstance(payload, dict):
            raise DataGenClientError("DataGenService beklenmeyen yanit formati dondu.")
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
