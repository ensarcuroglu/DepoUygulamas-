"""AI Asistan proxy router.

WmsAiService (varsayılan: http://localhost:8001) için ince proxy katmanı.
Frontend, mevcut Bearer token akışıyla `/api/ai/*` üzerinden çağırır;
bu router admin guard sonrası isteği WmsAiService'e iletir.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import require_role
from app.core.config import get_settings
from models import Kullanici

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Asistan"])


class SorguIstegi(BaseModel):
    soru: str = Field(..., min_length=2, max_length=500)
    session_id: str | None = None
    debug: bool = False
    verbose: bool = False


class OturumIstegi(BaseModel):
    session_id: str


def _upstream_base_url() -> str:
    return get_settings().wms_ai_service_url.rstrip("/")


def _upstream_timeout() -> float:
    return get_settings().wms_ai_service_timeout


def _forward(method: str, path: str, *, json_body: dict | None = None) -> Any:
    url = f"{_upstream_base_url()}{path}"
    try:
        with httpx.Client(timeout=_upstream_timeout()) as client:
            response = client.request(method, url, json=json_body)
    except httpx.ConnectError as exc:
        logger.warning("WmsAiService erişilemedi: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI servisi şu anda erişilebilir değil.",
        ) from exc
    except httpx.TimeoutException as exc:
        logger.warning("WmsAiService zaman aşımı: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI servisi yanıt vermedi (zaman aşımı).",
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("WmsAiService bilinmeyen hata")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"AI servisi hatası: {exc}",
        ) from exc

    if response.status_code >= 400:
        try:
            payload = response.json()
            detail = payload.get("detail") if isinstance(payload, dict) else payload
        except ValueError:
            detail = response.text
        raise HTTPException(status_code=response.status_code, detail=detail)

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI servisi geçersiz yanıt döndürdü.",
        ) from exc


@router.post("/sorgula")
def ai_sorgula(
    istek: SorguIstegi,
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    return _forward("POST", "/api/ai/sorgula", json_body=istek.model_dump())


@router.post("/oturum/sifirla")
def ai_oturum_sifirla(
    istek: OturumIstegi,
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    return _forward("POST", "/api/ai/oturum/sifirla", json_body=istek.model_dump())


@router.get("/sema")
def ai_sema(
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    return _forward("GET", "/api/ai/sema")
