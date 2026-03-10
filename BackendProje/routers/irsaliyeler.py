from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import require_role
from models import Kullanici
import crud
from schemas import (
    IrsaliyeCreate, IrsaliyeUpdate, IrsaliyeResponse
)

router = APIRouter(prefix="/api/irsaliyeler", tags=["İrsaliyeler"])


@router.get("/", response_model=list[IrsaliyeResponse])
def irsaliyeler_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Tüm irsaliyeleri listeler (filtreleme ve arama destekli)."""
    return crud.get_irsaliyeler(db, skip=skip, limit=limit, durum=durum, arama=arama)


@router.get("/{irsaliye_id}", response_model=IrsaliyeResponse)
def irsaliye_detay(
    irsaliye_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Belirli bir irsaliyenin detaylarını getirir."""
    db_irsaliye = crud.get_irsaliye(db, irsaliye_id)
    if not db_irsaliye:
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    return db_irsaliye


@router.post("/", response_model=IrsaliyeResponse, status_code=201)
def irsaliye_ekle(
    irsaliye: IrsaliyeCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Yeni bir irsaliye oluşturur (otomatik no üretimi)."""
    # Sipariş var mı kontrol et
    db_siparis = crud.get_siparis(db, irsaliye.siparis_id)
    if not db_siparis:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")

    return crud.create_irsaliye(db, irsaliye, kullanici_id=current_user.id)


@router.put("/{irsaliye_id}", response_model=IrsaliyeResponse)
def irsaliye_guncelle(
    irsaliye_id: int,
    irsaliye_update: IrsaliyeUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Mevcut bir irsaliyeyi günceller/durum değiştirir."""
    db_irsaliye = crud.update_irsaliye(db, irsaliye_id, irsaliye_update, kullanici_id=current_user.id)
    if not db_irsaliye:
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    return db_irsaliye
