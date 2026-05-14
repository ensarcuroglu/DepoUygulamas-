"""Excel yorumlama ve sema esleme endpoint'leri."""

from __future__ import annotations

import logging
from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from app.application.agents.pandas_qa_agent import PandasQaAgent
from app.application.use_cases.excel_sema_esle_uc import ExcelSemaEsleUseCase
from app.application.use_cases.excel_yorumla_uc import ExcelYorumlaUseCase
from app.core.config import Settings, get_settings
from app.core.entities.wms_target_schemas import list_target_schemas
from app.core.services.idempotency_cache import IdempotencyCache
from app.infrastructure.llm.ollama_client import get_chat_llm
from app.infrastructure.parsing.excel_loader import (
    CorruptWorkbookError,
    EmptyWorkbookError,
    ExcelLoader,
    FileTooLargeError,
    TooManyRowsError,
    TooManySheetsError,
    UnsupportedFileFormatError,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/excel", tags=["Excel"])

_CACHE: IdempotencyCache | None = None


def _get_cache(settings: Settings = Depends(get_settings)) -> IdempotencyCache:
    global _CACHE
    if _CACHE is None:
        _CACHE = IdempotencyCache(
            max_entries=settings.idempotency_max_entries,
            ttl_seconds=settings.idempotency_ttl_seconds,
        )
    return _CACHE


def _get_loader(settings: Settings = Depends(get_settings)) -> ExcelLoader:
    return ExcelLoader(settings)


def _get_yorumla_uc(
    settings: Settings = Depends(get_settings),
    loader: ExcelLoader = Depends(_get_loader),
) -> ExcelYorumlaUseCase:
    agent = PandasQaAgent(get_chat_llm(settings))
    return ExcelYorumlaUseCase(loader=loader, agent=agent)


def _get_sema_esle_uc(
    loader: ExcelLoader = Depends(_get_loader),
) -> ExcelSemaEsleUseCase:
    return ExcelSemaEsleUseCase(loader=loader)


@router.get("/hedef-semalar")
def list_schemas() -> dict:
    """Desteklenen WMS hedef semalarini listele."""
    schemas = list_target_schemas()
    return {
        "schemas": [
            {
                "name": s.name,
                "label": s.label,
                "fields": [
                    {
                        "name": f.name,
                        "aliases": list(f.aliases),
                        "required": f.required,
                        "description": f.description,
                    }
                    for f in s.fields
                ],
            }
            for s in schemas
        ]
    }


@router.post("/yorumla")
async def yorumla(
    file: UploadFile = File(...),
    soru: str | None = Form(default=None),
    sheet_name: str | None = Form(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    uc: ExcelYorumlaUseCase = Depends(_get_yorumla_uc),
    cache: IdempotencyCache = Depends(_get_cache),
) -> dict:
    if idempotency_key:
        cached = cache.get(idempotency_key)
        if cached is not None:
            return cached

    content = await file.read()
    try:
        result = uc.execute(
            filename=file.filename or "upload.xlsx",
            content=content,
            question=soru,
            sheet_name=sheet_name,
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except (UnsupportedFileFormatError, EmptyWorkbookError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (TooManySheetsError, TooManyRowsError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except CorruptWorkbookError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    payload = asdict(result)
    key = idempotency_key or result.idempotency_key
    cache.set(key, payload)
    return payload


@router.post("/sema-esle")
async def sema_esle(
    file: UploadFile = File(...),
    hedef_sema: str = Form(...),
    sheet_name: str | None = Form(default=None),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    uc: ExcelSemaEsleUseCase = Depends(_get_sema_esle_uc),
    cache: IdempotencyCache = Depends(_get_cache),
) -> dict:
    if idempotency_key:
        cached = cache.get(idempotency_key)
        if cached is not None:
            return cached

    content = await file.read()
    try:
        result = uc.execute(
            filename=file.filename or "upload.xlsx",
            content=content,
            target_schema=hedef_sema,
            sheet_name=sheet_name,
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except (UnsupportedFileFormatError, EmptyWorkbookError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (TooManySheetsError, TooManyRowsError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except CorruptWorkbookError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    payload = asdict(result)
    key = idempotency_key or result.idempotency_key
    cache.set(key, payload)
    return payload
