"""
Global Exception Handlers
Tüm APIException'ları ve Domain Exception'larını yakalar
ve standart JSON yanıtı döner.

Domain exception'ları (app.core.exceptions) → HTTP status code dönüşümü:
  KayitBulunamadiError      → 404
  YetersizStokError         → 400
  CakismaHatasi             → 409
  YetkisizIslemError        → 403
  GecersizDurumGecisiError  → 400
  GecersizIslemError        → 400
  StokVeriUyumsuzluguError  → 500
  DomainException (genel)   → 400
"""
import logging
from datetime import datetime

from fastapi import HTTPException as FastAPIHTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .exceptions import APIException

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# MEVCUT LEGACY HANDLER'LAR
# ═══════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════
# DOMAIN EXCEPTION → HTTP HANDLER'LAR
# ═══════════════════════════════════════════════════════════════

def _domain_json(status_code: int, mesaj: str, details: dict = None) -> JSONResponse:
    """Domain exception'ları için standart JSON response üretir."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": mesaj,
            "code": status_code,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        },
    )


async def kayit_bulunamadi_handler(request: Request, exc) -> JSONResponse:
    """KayitBulunamadiError → 404"""
    return _domain_json(404, exc.mesaj, {
        "entity": getattr(exc, "entity_adi", ""),
        "id": str(getattr(exc, "entity_id", "")),
    })


async def yetersiz_stok_handler(request: Request, exc) -> JSONResponse:
    """YetersizStokError → 400"""
    return _domain_json(400, exc.mesaj, {
        "urun": getattr(exc, "urun_ismi", ""),
        "mevcut": getattr(exc, "mevcut", 0),
        "istenen": getattr(exc, "istenen", 0),
    })


async def cakisma_handler(request: Request, exc) -> JSONResponse:
    """CakismaHatasi → 409"""
    return _domain_json(409, exc.mesaj, {
        "alan": getattr(exc, "alan", ""),
        "deger": getattr(exc, "deger", ""),
    })


async def yetkisiz_islem_handler(request: Request, exc) -> JSONResponse:
    """YetkisizIslemError → 403"""
    return _domain_json(403, exc.mesaj)


async def gecersiz_durum_gecisi_handler(request: Request, exc) -> JSONResponse:
    """GecersizDurumGecisiError → 400"""
    return _domain_json(400, exc.mesaj)


async def gecersiz_islem_handler(request: Request, exc) -> JSONResponse:
    """GecersizIslemError → 400"""
    return _domain_json(400, exc.mesaj)


async def stok_veri_uyumsuzlugu_handler(request: Request, exc) -> JSONResponse:
    """StokVeriUyumsuzluguError → 500 (veri bütünlüğü sorunu)"""
    logger.error(f"Stok veri uyumsuzluğu: {exc.mesaj}")
    return _domain_json(500, exc.mesaj)


async def domain_exception_handler(request: Request, exc) -> JSONResponse:
    """DomainException (catch-all) → 400"""
    return _domain_json(400, exc.mesaj)
