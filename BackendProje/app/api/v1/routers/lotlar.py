"""
Lot API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List, Optional

from app.core.auth import get_current_user, require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_lot_listele_uc,
    get_lot_getir_uc,
    get_lot_skt_yaklasan_uc,
    get_lot_olustur_uc,
    get_lot_guncelle_uc,
    get_lot_sil_uc,
)
from app.application.dto.lot_dto import (
    LotOlusturRequestDTO,
    LotGuncelleRequestDTO,
    LotResponseDTO,
)
from app.application.use_cases.lot_use_cases import (
    LotListeleUseCase,
    LotGetirUseCase,
    LotSktYaklasanUseCase,
    LotOlusturUseCase,
    LotGuncelleUseCase,
    LotSilUseCase,
)

router = APIRouter(prefix="/api/lotlar", tags=["Lotlar"])


@router.get("/", response_model=List[LotResponseDTO])
@limiter.limit("100/minute")
def lotlari_listele(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    urun_id: Optional[int] = Query(None, description="Ürüne göre filtrele"),
    current_user: Kullanici = Depends(get_current_user),
    uc: LotListeleUseCase = Depends(get_lot_listele_uc),
):
    return uc.execute(skip=skip, limit=limit, urun_id=urun_id)


@router.get("/skt-yaklasan", response_model=List[LotResponseDTO])
@limiter.limit("100/minute")
def skt_yaklasan_lotlar(
    request: Request,
    gun: int = Query(30, ge=1, le=365, description="Kaç gün içinde dolacak SKT'leri getir"),
    current_user: Kullanici = Depends(get_current_user),
    uc: LotSktYaklasanUseCase = Depends(get_lot_skt_yaklasan_uc),
):
    return uc.execute(gun=gun)


@router.get("/{lot_id}", response_model=LotResponseDTO)
@limiter.limit("100/minute")
def lot_detay(
    request: Request,
    lot_id: int,
    current_user: Kullanici = Depends(get_current_user),
    uc: LotGetirUseCase = Depends(get_lot_getir_uc),
):
    return uc.execute(lot_id)


@router.post("/", response_model=LotResponseDTO, status_code=201)
@limiter.limit("50/minute")
def lot_ekle(
    request: Request,
    lot: LotOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: LotOlusturUseCase = Depends(get_lot_olustur_uc),
):
    return uc.execute(lot, kullanici_id=current_user.id)


@router.put("/{lot_id}", response_model=LotResponseDTO)
@limiter.limit("50/minute")
def lot_guncelle(
    request: Request,
    lot_id: int,
    lot: LotGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: LotGuncelleUseCase = Depends(get_lot_guncelle_uc),
):
    return uc.execute(lot_id, lot, kullanici_id=current_user.id)


@router.delete("/{lot_id}")
@limiter.limit("50/minute")
def lot_sil(
    request: Request,
    lot_id: int,
    current_user: Kullanici = Depends(require_role("admin")),
    uc: LotSilUseCase = Depends(get_lot_sil_uc),
):
    uc.execute(lot_id, kullanici_id=current_user.id)
    return {"success": True, "message": "LOT başarıyla pasife alındı", "id": lot_id}
