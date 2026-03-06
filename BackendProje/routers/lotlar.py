from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import get_current_user, require_role
from models import Kullanici
import crud
from schemas import LotCreate, LotUpdate, LotResponse, LotDetailResponse

router = APIRouter(prefix="/api/lotlar", tags=["Lotlar"])


@router.get("/", response_model=list[LotDetailResponse])
def lotlari_listele(
    skip: int = 0,
    limit: int = 50,
    urun_id: Optional[int] = Query(None, description="Ürüne göre filtrele"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """LOT kayıtlarını listeler. Ürüne göre filtreleme destekler."""
    return crud.get_lotlar(db, skip=skip, limit=limit, urun_id=urun_id)


@router.get("/skt-yaklasan", response_model=list[LotDetailResponse])
def skt_yaklasan_lotlar(
    gun: int = Query(30, description="Kaç gün içinde dolacak SKT'leri getir"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Son kullanma tarihi yaklaşan LOT'ları listeler."""
    return crud.get_skt_yaklasan_lotlar(db, gun=gun)


@router.get("/{lot_id}", response_model=LotDetailResponse)
def lot_detay(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Belirli bir LOT'un detaylarını getirir."""
    db_lot = crud.get_lot(db, lot_id)
    if not db_lot:
        raise HTTPException(status_code=404, detail="LOT bulunamadı")
    return db_lot


@router.post("/", response_model=LotResponse, status_code=201)
def lot_ekle(
    lot: LotCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni bir LOT kaydı oluşturur. Sadece admin."""
    # Ürün var mı kontrol et
    db_urun = crud.get_urun(db, lot.urun_id)
    if not db_urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return crud.create_lot(db, lot)


@router.put("/{lot_id}", response_model=LotResponse)
def lot_guncelle(
    lot_id: int,
    lot: LotUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Mevcut bir LOT kaydını günceller. Sadece admin."""
    db_lot = crud.update_lot(db, lot_id, lot)
    if not db_lot:
        raise HTTPException(status_code=404, detail="LOT bulunamadı")
    return db_lot


@router.delete("/{lot_id}")
def lot_sil(
    lot_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Bir LOT kaydını pasife alır. Sadece admin."""
    success = crud.delete_lot(db, lot_id)
    if not success:
        raise HTTPException(status_code=404, detail="LOT bulunamadı")
    return {"message": "LOT başarıyla pasife alındı", "id": lot_id}
