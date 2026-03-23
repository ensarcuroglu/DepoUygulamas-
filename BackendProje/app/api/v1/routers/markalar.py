"""
Marka API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List

from auth import require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_marka_listele_uc,
    get_marka_getir_uc,
    get_marka_olustur_uc,
    get_marka_guncelle_uc,
    get_marka_sil_uc,
)
from app.application.dto.marka_dto import (
    MarkaOlusturRequestDTO,
    MarkaGuncelleRequestDTO,
    MarkaResponseDTO,
)
from app.application.use_cases.marka_use_cases import (
    MarkaListeleUseCase,
    MarkaGetirUseCase,
    MarkaOlusturUseCase,
    MarkaGuncelleUseCase,
    MarkaSilUseCase,
)

router = APIRouter(prefix="/api/markalar", tags=["Markalar"])


@router.get("/", response_model=List[MarkaResponseDTO])
@limiter.limit("100/minute")
def markalari_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: Kullanici = Depends(require_role("admin")),
    uc: MarkaListeleUseCase = Depends(get_marka_listele_uc),
):
    return uc.execute(skip=skip, limit=limit)


@router.get("/{marka_id}", response_model=MarkaResponseDTO)
@limiter.limit("100/minute")
def marka_detay(
    request: Request,
    marka_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: MarkaGetirUseCase = Depends(get_marka_getir_uc),
):
    return uc.execute(marka_id)


@router.post("/", response_model=MarkaResponseDTO, status_code=201)
@limiter.limit("50/minute")
def marka_ekle(
    request: Request,
    marka: MarkaOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: MarkaOlusturUseCase = Depends(get_marka_olustur_uc),
):
    return uc.execute(marka, kullanici_id=current_user.id)


@router.put("/{marka_id}", response_model=MarkaResponseDTO)
@limiter.limit("50/minute")
def marka_guncelle(
    request: Request,
    marka_id: int,
    marka: MarkaGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: MarkaGuncelleUseCase = Depends(get_marka_guncelle_uc),
):
    return uc.execute(marka_id, marka, kullanici_id=current_user.id)


@router.delete("/{marka_id}")
@limiter.limit("50/minute")
def marka_sil(
    request: Request,
    marka_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: MarkaSilUseCase = Depends(get_marka_sil_uc),
):
    uc.execute(marka_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Marka başarıyla pasife alındı", "id": marka_id}
