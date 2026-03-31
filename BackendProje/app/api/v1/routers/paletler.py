"""
Palet API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional

from app.core.auth import get_current_user, require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_palet_listele_uc,
    get_palet_getir_uc,
    get_palet_barkod_ile_getir_uc,
    get_palet_sonraki_numara_uc,
    get_palet_olustur_uc,
    get_palet_guncelle_uc,
    get_palet_sil_uc,
)
from app.application.dto.palet_dto import (
    PaletOlusturRequestDTO,
    PaletGuncelleRequestDTO,
    PaletResponseDTO,
)
from app.application.use_cases.palet_use_cases import (
    PaletListeleUseCase,
    PaletGetirUseCase,
    PaletBarkodIleGetirUseCase,
    PaletSonrakiNumaraUseCase,
    PaletOlusturUseCase,
    PaletGuncelleUseCase,
    PaletSilUseCase,
)

router = APIRouter(prefix="/api/paletler", tags=["Paletler"])


@router.get("/", response_model=List[PaletResponseDTO])
@limiter.limit("100/minute")
def paletleri_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    lot_id: Optional[int] = Query(None, description="LOT'a göre filtrele"),
    raf_id: Optional[int] = Query(None, description="Rafa göre filtrele"),
    current_user: Kullanici = Depends(get_current_user),
    uc: PaletListeleUseCase = Depends(get_palet_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, lot_id=lot_id, raf_id=raf_id)


@router.get("/sonraki-numara")
@limiter.limit("100/minute")
def sonraki_palet_numarasi(
    request: Request,
    current_user: Kullanici = Depends(get_current_user),
    uc: PaletSonrakiNumaraUseCase = Depends(get_palet_sonraki_numara_uc),
):
    return {"palet_no": uc.execute()}


@router.get("/barkod/{palet_no}", response_model=PaletResponseDTO)
@limiter.limit("100/minute")
def palet_getir_by_barkod(
    request: Request,
    palet_no: str,
    current_user: Kullanici = Depends(get_current_user),
    uc: PaletBarkodIleGetirUseCase = Depends(get_palet_barkod_ile_getir_uc),
):
    return uc.execute(palet_no)


@router.get("/{palet_id}", response_model=PaletResponseDTO)
@limiter.limit("100/minute")
def palet_detay(
    request: Request,
    palet_id: int,
    current_user: Kullanici = Depends(get_current_user),
    uc: PaletGetirUseCase = Depends(get_palet_getir_uc),
):
    return uc.execute(palet_id)


@router.post("/", response_model=PaletResponseDTO, status_code=201)
@limiter.limit("50/minute")
def palet_ekle(
    request: Request,
    palet: PaletOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: PaletOlusturUseCase = Depends(get_palet_olustur_uc),
):
    return uc.execute(palet, kullanici_id=current_user.id)


@router.put("/{palet_id}", response_model=PaletResponseDTO)
@limiter.limit("50/minute")
def palet_guncelle(
    request: Request,
    palet_id: int,
    palet: PaletGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: PaletGuncelleUseCase = Depends(get_palet_guncelle_uc),
):
    return uc.execute(palet_id, palet, kullanici_id=current_user.id)


@router.delete("/{palet_id}")
@limiter.limit("50/minute")
def palet_sil(
    request: Request,
    palet_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: PaletSilUseCase = Depends(get_palet_sil_uc),
):
    uc.execute(palet_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Palet başarıyla pasife alındı", "id": palet_id}
