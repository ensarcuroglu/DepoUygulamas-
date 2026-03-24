"""
İrsaliye API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional, List

from auth import require_role
from models import Kullanici

from app.infrastructure.di.container import (
    get_irsaliye_listele_uc,
    get_irsaliye_getir_uc,
    get_irsaliye_olustur_uc,
    get_irsaliye_guncelle_uc,
    get_irsaliye_yazdir_uc,
)

from app.application.dto import (
    IrsaliyeOlusturRequestDTO,
    IrsaliyeGuncelleRequestDTO,
    IrsaliyeResponseDTO,
    IrsaliyeYazdirResponseDTO,
)

from app.application.use_cases import (
    IrsaliyeListeleUseCase,
    IrsaliyeGetirUseCase,
    IrsaliyeOlusturUseCase,
    IrsaliyeGuncelleUseCase,
    IrsaliyeYazdirVerisiGetirUseCase,
)

router = APIRouter(prefix="/api/irsaliyeler", tags=["İrsaliyeler"])


@router.get("/", response_model=List[IrsaliyeResponseDTO])
def irsaliyeler_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: IrsaliyeListeleUseCase = Depends(get_irsaliye_listele_uc),
):
    """İrsaliye listesini döner. Durum ve arama filtresi destekler."""
    return uc.execute(skip=skip, limit=limit, durum=durum, arama=arama)


@router.get("/{irsaliye_id}", response_model=IrsaliyeResponseDTO)
def irsaliye_detay(
    irsaliye_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: IrsaliyeGetirUseCase = Depends(get_irsaliye_getir_uc),
):
    """Tek irsaliye detay bilgisini döner."""
    return uc.execute(irsaliye_id)


@router.post("/", response_model=IrsaliyeResponseDTO, status_code=201)
def irsaliye_ekle(
    irsaliye: IrsaliyeOlusturRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: IrsaliyeOlusturUseCase = Depends(get_irsaliye_olustur_uc),
):
    """Yeni irsaliye oluşturur. Otomatik irsaliye numarası atanır."""
    return uc.execute(irsaliye, kullanici_id=current_user.id)


@router.put("/{irsaliye_id}", response_model=IrsaliyeResponseDTO)
def irsaliye_guncelle(
    irsaliye_id: int,
    irsaliye_update: IrsaliyeGuncelleRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: IrsaliyeGuncelleUseCase = Depends(get_irsaliye_guncelle_uc),
):
    """İrsaliye bilgilerini ve durumunu günceller."""
    return uc.execute(irsaliye_id, irsaliye_update, kullanici_id=current_user.id)


@router.get("/{irsaliye_id}/yazdir", response_model=IrsaliyeYazdirResponseDTO)
def irsaliye_yazdir_verisi(
    irsaliye_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: IrsaliyeYazdirVerisiGetirUseCase = Depends(get_irsaliye_yazdir_uc),
):
    """İrsaliye yazdırma verisi: irsaliye + sipariş + kalemler."""
    return uc.execute(irsaliye_id)
