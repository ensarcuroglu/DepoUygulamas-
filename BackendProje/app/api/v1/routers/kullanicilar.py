"""
Kullanıcı Yönetimi API Router — Clean Architecture (Thin Controller).

NOT: Login/register auth.py router'ında kalır.
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional

from auth import get_current_user, require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_kullanici_listele_uc,
    get_kullanici_getir_uc,
    get_kullanici_guncelle_uc,
    get_kullanici_sil_uc,
)
from app.application.dto.kullanici_dto import (
    KullaniciGuncelleRequestDTO,
    KullaniciResponseDTO,
)
from app.application.use_cases.kullanici_use_cases import (
    KullaniciListeleUseCase,
    KullaniciGetirUseCase,
    KullaniciGuncelleUseCase,
    KullaniciSilUseCase,
)

router = APIRouter(prefix="/api/kullanicilar", tags=["Kullanıcı Yönetimi"])


@router.get("/", response_model=List[KullaniciResponseDTO])
@limiter.limit("100/minute")
def kullanicilari_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KullaniciListeleUseCase = Depends(get_kullanici_listele_uc),
):
    return uc.execute(skip=skip, limit=limit)


@router.get("/{kullanici_id}", response_model=KullaniciResponseDTO)
@limiter.limit("100/minute")
def kullanici_detay(
    request: Request,
    kullanici_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KullaniciGetirUseCase = Depends(get_kullanici_getir_uc),
):
    return uc.execute(kullanici_id)


@router.put("/{kullanici_id}", response_model=KullaniciResponseDTO)
@limiter.limit("50/minute")
def kullanici_guncelle(
    request: Request,
    kullanici_id: int,
    data: KullaniciGuncelleRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: KullaniciGuncelleUseCase = Depends(get_kullanici_guncelle_uc),
):
    return uc.execute(kullanici_id, data, current_user=current_user)


@router.delete("/{kullanici_id}")
@limiter.limit("50/minute")
def kullanici_sil(
    request: Request,
    kullanici_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KullaniciSilUseCase = Depends(get_kullanici_sil_uc),
):
    uc.execute(kullanici_id, current_user=current_user)
    return {"success": True, "message": "Kullanıcı başarıyla silindi", "id": kullanici_id}
