"""
Global Exception Handlers
==========================

Tum APIException alt siniflarini (legacy + domain) tek bir handler ile yakalar
ve standart JSON yaniti doner.

Artik domain exception'lar da APIException'dan turedigi icin
her biri icin ayri handler kaydetmeye gerek yoktur.
"""
import logging
from datetime import datetime

from fastapi import HTTPException as FastAPIHTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .api_exceptions import APIException

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    Tum APIException alt siniflarini yakalar ve standart yanit doner.
    Legacy (NotFoundError, DuplicateError, ...) ve domain (KayitBulunamadiError,
    YetersizStokError, ...) exception'lari ayni formatta doner.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
            "code": exc.status_code,
            "details": exc.details,
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Beklenmeyen sunucu hatalari icin fallback handler.
    FastAPI/Starlette'nin kendi HTTPException ve RequestValidationError
    handler'larini gecersiz kilmaz; onlari yeniden yukseltir.
    """
    if isinstance(exc, (FastAPIHTTPException, RequestValidationError)):
        raise exc

    logger.exception(f"Beklenmeyen hata — {request.method} {request.url}: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Sunucu hatası oluştu",
            "code": 500,
            "details": {},
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
