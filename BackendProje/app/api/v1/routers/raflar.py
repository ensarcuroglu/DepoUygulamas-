"""
Raf API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional

from app.core.auth import require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_raf_listele_uc,
    get_raf_getir_uc,
    get_raf_olustur_uc,
    get_raf_guncelle_uc,
    get_raf_sil_uc,
)
from app.application.dto.raf_dto import (
    RafOlusturRequestDTO,
    RafGuncelleRequestDTO,
    RafResponseDTO,
)
from app.application.use_cases.raf_use_cases import (
    RafListeleUseCase,
    RafGetirUseCase,
    RafOlusturUseCase,
    RafGuncelleUseCase,
    RafSilUseCase,
)

router = APIRouter(prefix="/api/raflar", tags=["Raflar"])


@router.get("/", response_model=List[RafResponseDTO])
@limiter.limit("100/minute")
def raflari_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=500, ge=1, le=1000),
    depo_id: Optional[int] = None,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: RafListeleUseCase = Depends(get_raf_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, depo_id=depo_id)


@router.get("/{raf_id}", response_model=RafResponseDTO)
@limiter.limit("100/minute")
def raf_detay(
    request: Request,
    raf_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: RafGetirUseCase = Depends(get_raf_getir_uc),
):
    return uc.execute(raf_id)


@router.post("/", response_model=RafResponseDTO, status_code=201)
@limiter.limit("50/minute")
def raf_ekle(
    request: Request,
    raf: RafOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RafOlusturUseCase = Depends(get_raf_olustur_uc),
):
    return uc.execute(raf, kullanici_id=current_user.id)


@router.put("/{raf_id}", response_model=RafResponseDTO)
@limiter.limit("50/minute")
def raf_guncelle(
    request: Request,
    raf_id: int,
    raf: RafGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RafGuncelleUseCase = Depends(get_raf_guncelle_uc),
):
    return uc.execute(raf_id, raf, kullanici_id=current_user.id)


@router.delete("/{raf_id}")
@limiter.limit("50/minute")
def raf_sil(
    request: Request,
    raf_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RafSilUseCase = Depends(get_raf_sil_uc),
):
    uc.execute(raf_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Raf başarıyla pasife alındı", "id": raf_id}
