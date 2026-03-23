"""
Destek Masası API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional

from auth import get_current_user, require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_destek_listele_uc,
    get_destek_getir_uc,
    get_destek_olustur_uc,
    get_destek_guncelle_uc,
)
from app.application.dto.destek_talebi_dto import (
    DestekTalebiOlusturRequestDTO,
    DestekTalebiGuncelleRequestDTO,
    DestekTalebiResponseDTO,
)
from app.application.use_cases.destek_talebi_use_cases import (
    DestekTalebiListeleUseCase,
    DestekTalebiGetirUseCase,
    DestekTalebiOlusturUseCase,
    DestekTalebiGuncelleUseCase,
)

router = APIRouter(prefix="/api/destek", tags=["Destek Masası"])


@router.get("/", response_model=List[DestekTalebiResponseDTO])
@limiter.limit("100/minute")
def get_destek_talepleri(
    request: Request,
    durum: Optional[str] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: Kullanici = Depends(get_current_user),
    uc: DestekTalebiListeleUseCase = Depends(get_destek_listele_uc),
):
    return uc.execute(current_user=current_user, skip=skip, limit=limit, durum=durum)


@router.get("/{talep_id}", response_model=DestekTalebiResponseDTO)
@limiter.limit("100/minute")
def get_destek_talebi(
    request: Request,
    talep_id: int,
    current_user: Kullanici = Depends(get_current_user),
    uc: DestekTalebiGetirUseCase = Depends(get_destek_getir_uc),
):
    return uc.execute(talep_id, current_user=current_user)


@router.post("/", response_model=DestekTalebiResponseDTO)
@limiter.limit("50/minute")
def create_destek_talebi(
    request: Request,
    talep: DestekTalebiOlusturRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: DestekTalebiOlusturUseCase = Depends(get_destek_olustur_uc),
):
    return uc.execute(talep, kullanici_id=current_user.id)


@router.put("/{talep_id}", response_model=DestekTalebiResponseDTO)
@limiter.limit("50/minute")
def update_destek_talebi(
    request: Request,
    talep_id: int,
    talep_update: DestekTalebiGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: DestekTalebiGuncelleUseCase = Depends(get_destek_guncelle_uc),
):
    return uc.execute(talep_id, talep_update, admin_id=current_user.id)
