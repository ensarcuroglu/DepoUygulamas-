"""
Tedarikçi API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List

from auth import require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_tedarikci_listele_uc,
    get_tedarikci_getir_uc,
    get_tedarikci_olustur_uc,
    get_tedarikci_guncelle_uc,
    get_tedarikci_sil_uc,
)
from app.application.dto.tedarikci_dto import (
    TedarikciOlusturRequestDTO,
    TedarikciGuncelleRequestDTO,
    TedarikciResponseDTO,
)
from app.application.use_cases.tedarikci_use_cases import (
    TedarikciListeleUseCase,
    TedarikciGetirUseCase,
    TedarikciOlusturUseCase,
    TedarikciGuncelleUseCase,
    TedarikciSilUseCase,
)

router = APIRouter(prefix="/api/tedarikciler", tags=["Tedarikçiler"])


@router.get("/", response_model=List[TedarikciResponseDTO])
@limiter.limit("100/minute")
def tedarikcileri_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: Kullanici = Depends(require_role("admin")),
    uc: TedarikciListeleUseCase = Depends(get_tedarikci_listele_uc),
):
    return uc.execute(skip=skip, limit=limit)


@router.get("/{tedarikci_id}", response_model=TedarikciResponseDTO)
@limiter.limit("100/minute")
def tedarikci_detay(
    request: Request,
    tedarikci_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: TedarikciGetirUseCase = Depends(get_tedarikci_getir_uc),
):
    return uc.execute(tedarikci_id)


@router.post("/", response_model=TedarikciResponseDTO, status_code=201)
@limiter.limit("50/minute")
def tedarikci_olustur(
    request: Request,
    tedarikci: TedarikciOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: TedarikciOlusturUseCase = Depends(get_tedarikci_olustur_uc),
):
    return uc.execute(tedarikci, kullanici_id=current_user.id)


@router.put("/{tedarikci_id}", response_model=TedarikciResponseDTO)
@limiter.limit("50/minute")
def tedarikci_guncelle(
    request: Request,
    tedarikci_id: int,
    tedarikci: TedarikciGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: TedarikciGuncelleUseCase = Depends(get_tedarikci_guncelle_uc),
):
    return uc.execute(tedarikci_id, tedarikci, kullanici_id=current_user.id)


@router.delete("/{tedarikci_id}")
@limiter.limit("50/minute")
def tedarikci_sil(
    request: Request,
    tedarikci_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: TedarikciSilUseCase = Depends(get_tedarikci_sil_uc),
):
    uc.execute(tedarikci_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Tedarikçi başarıyla pasife alındı", "id": tedarikci_id}
