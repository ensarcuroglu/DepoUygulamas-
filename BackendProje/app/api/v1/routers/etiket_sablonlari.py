"""Etiket Şablonu API Router — admin-only CRUD."""

from typing import List

from fastapi import APIRouter, Depends, Query, Request

from app.core.auth import get_current_user, require_role
from app.infrastructure.persistence.mappers.kullanici_destek_mapper import kullanici_to_entity
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_etiket_sablonlari_listele_uc,
    get_etiket_sablonu_getir_uc,
    get_etiket_sablonu_olustur_uc,
    get_etiket_sablonu_guncelle_uc,
    get_etiket_sablonu_sil_uc,
)
from app.application.dto.etiket_dto import (
    EtiketSablonuOlusturDTO,
    EtiketSablonuGuncelleDTO,
    EtiketSablonuResponseDTO,
)
from app.application.use_cases.etiket_sablonu_use_cases import (
    EtiketSablonlariListeleUseCase,
    EtiketSablonuGetirUseCase,
    EtiketSablonuOlusturUseCase,
    EtiketSablonuGuncelleUseCase,
    EtiketSablonuSilUseCase,
)

router = APIRouter(prefix="/api/etiket-sablonlari", tags=["Etiket Şablonları"])


@router.get("/", response_model=List[EtiketSablonuResponseDTO])
@limiter.limit("100/minute")
def sablonlari_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    sadece_aktif: bool = Query(True),
    current_user: Kullanici = Depends(get_current_user),
    uc: EtiketSablonlariListeleUseCase = Depends(get_etiket_sablonlari_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, sadece_aktif=sadece_aktif)


@router.get("/{sablon_id}", response_model=EtiketSablonuResponseDTO)
@limiter.limit("100/minute")
def sablon_detay(
    request: Request,
    sablon_id: int,
    current_user: Kullanici = Depends(get_current_user),
    uc: EtiketSablonuGetirUseCase = Depends(get_etiket_sablonu_getir_uc),
):
    return uc.execute(sablon_id)


@router.post("/", response_model=EtiketSablonuResponseDTO, status_code=201)
@limiter.limit("50/minute")
def sablon_olustur(
    request: Request,
    dto: EtiketSablonuOlusturDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: EtiketSablonuOlusturUseCase = Depends(get_etiket_sablonu_olustur_uc),
):
    return uc.execute(dto, kullanici_to_entity(current_user))


@router.put("/{sablon_id}", response_model=EtiketSablonuResponseDTO)
@limiter.limit("50/minute")
def sablon_guncelle(
    request: Request,
    sablon_id: int,
    dto: EtiketSablonuGuncelleDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: EtiketSablonuGuncelleUseCase = Depends(get_etiket_sablonu_guncelle_uc),
):
    return uc.execute(sablon_id, dto, kullanici_to_entity(current_user))


@router.delete("/{sablon_id}")
@limiter.limit("50/minute")
def sablon_sil(
    request: Request,
    sablon_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: EtiketSablonuSilUseCase = Depends(get_etiket_sablonu_sil_uc),
):
    uc.execute(sablon_id, kullanici_to_entity(current_user))
    return {"success": True, "message": "Etiket şablonu pasife alındı", "id": sablon_id}
