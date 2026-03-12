from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Kullanici
from auth import get_current_user, require_role
from schemas import StokSayimRead, StokSayimKalemiRead, StokSayimCreate, StokSayimKalemiCreate
from services.stok_sayim_service import StokSayimService

router = APIRouter(prefix="/api/stok-sayimlar", tags=["stok-sayim"])


@router.get("", response_model=List[StokSayimRead])
def sayimlari_listele(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Tüm stok sayımlarını listeler."""
    return StokSayimService.get_sayimlar(db)


@router.get("/{sayim_id}", response_model=StokSayimRead)
def sayim_detayi(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    return StokSayimService.get_sayim(db, sayim_id)


@router.post("", response_model=StokSayimRead, status_code=201)
def sayim_basla(
    sayim_data: StokSayimCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Yeni stok sayımı oturumu başlatır; mevcut stok durumunu snapshot olarak kaydeder."""
    return StokSayimService.basla(db, sayim_data, kullanici_id=current_user.id)


@router.post("/{sayim_id}/kalemler", response_model=StokSayimKalemiRead)
def urun_sayisi_kaydet(
    sayim_id: int,
    kalem_data: StokSayimKalemiCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Belirli bir ürünün sayılan miktarını kaydeder (upsert)."""
    return StokSayimService.kalem_kaydet(db, sayim_id, kalem_data, kullanici_id=current_user.id)


@router.get("/{sayim_id}/varyans")
def varyans_hesapla(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Sayım kapatılırken beklenen stok ile sayılan miktarı karşılaştırır."""
    return StokSayimService.varyans_hesapla(db, sayim_id)


@router.post("/{sayim_id}/onayla")
def sayimi_onayla(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Sayımı kapatır ve 'onaylandı' durumuna geçirir."""
    return StokSayimService.onayla(db, sayim_id, kullanici_id=current_user.id)
