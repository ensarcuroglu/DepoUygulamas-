"""
Global Exception Handlers
Tüm APIException'ları yakalar ve standart JSON yanıtı döner.

Düzeltme (plan1.md'den):
  generic_exception_handler, FastAPI'nin kendi HTTPException ve
  RequestValidationError'larını geçersiz kılmamalıdır; bu nedenle
  isinstance kontrolü eklendi.
"""
import logging
from datetime import datetime

from fastapi import HTTPException as FastAPIHTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .exceptions import APIException

logger = logging.getLogger(__name__)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """APIException alt sınıflarını yakalar ve standart yanıt döner."""
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
    Beklenmeyen sunucu hataları için fallback handler.
    FastAPI/Starlette'nin kendi HTTPException ve RequestValidationError
    handler'larını geçersiz kılmaz; onları yeniden yükseltir.
    """
    # FastAPI/Starlette'nin native exception'larına dokunma
    if isinstance(exc, (FastAPIHTTPException, RequestValidationError)):
        raise exc

    # Beklenmeyen gerçek sunucu hatalarını logla
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
