"""
Depo API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List

from auth import require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_depo_listele_uc,
    get_depo_getir_uc,
    get_depo_olustur_uc,
    get_depo_guncelle_uc,
    get_depo_sil_uc,
)
from app.application.dto.depo_dto import (
    DepoOlusturRequestDTO,
    DepoGuncelleRequestDTO,
    DepoResponseDTO,
)
from app.application.use_cases.depo_use_cases import (
    DepoListeleUseCase,
    DepoGetirUseCase,
    DepoOlusturUseCase,
    DepoGuncelleUseCase,
    DepoSilUseCase,
)

router = APIRouter(prefix="/api/depolar", tags=["Depolar"])


@router.get("/", response_model=List[DepoResponseDTO])
@limiter.limit("100/minute")
def depolari_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: DepoListeleUseCase = Depends(get_depo_listele_uc),
):
    return uc.execute(skip=skip, limit=limit)


@router.get("/{depo_id}", response_model=DepoResponseDTO)
@limiter.limit("100/minute")
def depo_detay(
    request: Request,
    depo_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: DepoGetirUseCase = Depends(get_depo_getir_uc),
):
    return uc.execute(depo_id)


@router.post("/", response_model=DepoResponseDTO, status_code=201)
@limiter.limit("50/minute")
def depo_ekle(
    request: Request,
    depo: DepoOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: DepoOlusturUseCase = Depends(get_depo_olustur_uc),
):
    return uc.execute(depo, kullanici_id=current_user.id)


@router.put("/{depo_id}", response_model=DepoResponseDTO)
@limiter.limit("50/minute")
def depo_guncelle(
    request: Request,
    depo_id: int,
    depo: DepoGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: DepoGuncelleUseCase = Depends(get_depo_guncelle_uc),
):
    return uc.execute(depo_id, depo, kullanici_id=current_user.id)


@router.delete("/{depo_id}")
@limiter.limit("50/minute")
def depo_sil(
    request: Request,
    depo_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: DepoSilUseCase = Depends(get_depo_sil_uc),
):
    uc.execute(depo_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Depo başarıyla pasife alındı", "id": depo_id}
