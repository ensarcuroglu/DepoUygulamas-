"""
Zon API Router - Clean Architecture (Thin Controller).
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request

from app.application.dto.zon_dto import (
    ZonGuncelleRequestDTO,
    ZonOlusturRequestDTO,
    ZonResponseDTO,
)
from app.application.use_cases.zon_use_cases import (
    ZonGetirUseCase,
    ZonGuncelleUseCase,
    ZonListeleUseCase,
    ZonOlusturUseCase,
    ZonSilUseCase,
)
from app.core.auth import require_role
from app.infrastructure.di.container import (
    get_zon_getir_uc,
    get_zon_guncelle_uc,
    get_zon_listele_uc,
    get_zon_olustur_uc,
    get_zon_sil_uc,
)
from limiter import limiter
from models import Kullanici

router = APIRouter(prefix="/api/zonlar", tags=["Zonlar"])


@router.get("/", response_model=List[ZonResponseDTO])
@limiter.limit("100/minute")
def zonlari_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    depo_id: Optional[int] = None,
    tip: Optional[str] = None,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: ZonListeleUseCase = Depends(get_zon_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, depo_id=depo_id, tip=tip)


@router.get("/{zon_id}", response_model=ZonResponseDTO)
@limiter.limit("100/minute")
def zon_detay(
    request: Request,
    zon_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: ZonGetirUseCase = Depends(get_zon_getir_uc),
):
    return uc.execute(zon_id)


@router.post("/", response_model=ZonResponseDTO, status_code=201)
@limiter.limit("50/minute")
def zon_ekle(
    request: Request,
    zon: ZonOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: ZonOlusturUseCase = Depends(get_zon_olustur_uc),
):
    return uc.execute(zon, kullanici_id=current_user.id)


@router.put("/{zon_id}", response_model=ZonResponseDTO)
@limiter.limit("50/minute")
def zon_guncelle(
    request: Request,
    zon_id: int,
    zon: ZonGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: ZonGuncelleUseCase = Depends(get_zon_guncelle_uc),
):
    return uc.execute(zon_id, zon, kullanici_id=current_user.id)


@router.delete("/{zon_id}")
@limiter.limit("50/minute")
def zon_sil(
    request: Request,
    zon_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: ZonSilUseCase = Depends(get_zon_sil_uc),
):
    uc.execute(zon_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Zon basariyla pasife alindi", "id": zon_id}

