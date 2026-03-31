"""
Kategori API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List

from app.core.auth import require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_kategori_listele_uc,
    get_kategori_getir_uc,
    get_kategori_olustur_uc,
    get_kategori_guncelle_uc,
    get_kategori_sil_uc,
)
from app.application.dto.kategori_dto import (
    KategoriOlusturRequestDTO,
    KategoriGuncelleRequestDTO,
    KategoriResponseDTO,
)
from app.application.use_cases.kategori_use_cases import (
    KategoriListeleUseCase,
    KategoriGetirUseCase,
    KategoriOlusturUseCase,
    KategoriGuncelleUseCase,
    KategoriSilUseCase,
)

router = APIRouter(prefix="/api/kategoriler", tags=["Kategoriler"])


@router.get("/", response_model=List[KategoriResponseDTO])
@limiter.limit("100/minute")
def kategorileri_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KategoriListeleUseCase = Depends(get_kategori_listele_uc),
):
    return uc.execute(skip=skip, limit=limit)


@router.get("/{kategori_id}", response_model=KategoriResponseDTO)
@limiter.limit("100/minute")
def kategori_detay(
    request: Request,
    kategori_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KategoriGetirUseCase = Depends(get_kategori_getir_uc),
):
    return uc.execute(kategori_id)


@router.post("/", response_model=KategoriResponseDTO, status_code=201)
@limiter.limit("50/minute")
def kategori_ekle(
    request: Request,
    kategori: KategoriOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KategoriOlusturUseCase = Depends(get_kategori_olustur_uc),
):
    return uc.execute(kategori, kullanici_id=current_user.id)


@router.put("/{kategori_id}", response_model=KategoriResponseDTO)
@limiter.limit("50/minute")
def kategori_guncelle(
    request: Request,
    kategori_id: int,
    kategori: KategoriGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KategoriGuncelleUseCase = Depends(get_kategori_guncelle_uc),
):
    return uc.execute(kategori_id, kategori, kullanici_id=current_user.id)


@router.delete("/{kategori_id}")
@limiter.limit("50/minute")
def kategori_sil(
    request: Request,
    kategori_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: KategoriSilUseCase = Depends(get_kategori_sil_uc),
):
    uc.execute(kategori_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Kategori başarıyla pasife alındı", "id": kategori_id}
