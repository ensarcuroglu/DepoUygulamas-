"""ExcelAiService proxy router.

Bu router ExcelAiService'e (port 8004) ince bir proxy katmanidir.
Frontend mevcut Bearer token akisi ile `/api/excel-ai/*` cagirir;
backend admin guard sonrasi istegi internal HTTP ile ExcelAi'ye iletir.

ExcelAiService DB'ye yazmaz; BackendProje burada yalnizca yetki, feature
flag ve INTERNAL_API_KEY enjeksiyonu yapar.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from app.core.auth import require_role
from app.core.config import Settings, get_settings
from app.infrastructure.services.excel_ai_client import ExcelAiClient
from models import Kullanici

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/excel-ai", tags=["Excel AI"])


def _ensure_enabled(settings: Settings) -> None:
    if not settings.feature_excel_ai_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Excel AI ozelligi devre disi.",
        )


def _get_client(settings: Settings = Depends(get_settings)) -> ExcelAiClient:
    _ensure_enabled(settings)
    return ExcelAiClient(settings)


@router.get("/hedef-semalar")
def hedef_semalar(
    client: ExcelAiClient = Depends(_get_client),
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    return client.hedef_semalar()


@router.post("/yorumla")
async def yorumla(
    file: UploadFile = File(...),
    soru: Optional[str] = Form(default=None),
    sheet_name: Optional[str] = Form(default=None),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    client: ExcelAiClient = Depends(_get_client),
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    content = await file.read()
    return client.yorumla(
        filename=file.filename or "upload.xlsx",
        content_type=file.content_type,
        content=content,
        soru=soru,
        sheet_name=sheet_name,
        idempotency_key=idempotency_key,
    )


@router.post("/sema-esle")
async def sema_esle(
    file: UploadFile = File(...),
    hedef_sema: str = Form(...),
    sheet_name: Optional[str] = Form(default=None),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
    client: ExcelAiClient = Depends(_get_client),
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    content = await file.read()
    return client.sema_esle(
        filename=file.filename or "upload.xlsx",
        content_type=file.content_type,
        content=content,
        hedef_sema=hedef_sema,
        sheet_name=sheet_name,
        idempotency_key=idempotency_key,
    )
