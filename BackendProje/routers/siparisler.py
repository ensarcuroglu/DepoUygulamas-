from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import require_role, get_current_user
from models import Kullanici
import crud
from schemas import (
    SiparisCreate, SiparisUpdate, SiparisResponse, SiparisDetayResponse
)

router = APIRouter(prefix="/api/siparisler", tags=["Siparişler"])


@router.get("/", response_model=list[SiparisResponse])
def siparisler_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Tüm siparişleri listeler (filtreleme ve arama destekli)."""
    return crud.get_siparisler(db, skip=skip, limit=limit, durum=durum, arama=arama)


@router.get("/{siparis_id}", response_model=SiparisDetayResponse)
def siparis_detay(
    siparis_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Belirli bir siparişin detaylarını getirir (kalemlerle birlikte)."""
    db_siparis = crud.get_siparis(db, siparis_id)
    if not db_siparis:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    return db_siparis


@router.post("/", response_model=SiparisDetayResponse, status_code=201)
def siparis_ekle(
    siparis: SiparisCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Yeni bir sipariş oluşturur (kalemlerle birlikte)."""
    return crud.create_siparis(db, siparis, kullanici_id=current_user.id)


@router.put("/{siparis_id}", response_model=SiparisDetayResponse)
def siparis_guncelle(
    siparis_id: int,
    siparis_update: SiparisUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Mevcut bir siparişi günceller."""
    db_siparis = crud.update_siparis(db, siparis_id, siparis_update, kullanici_id=current_user.id)
    if not db_siparis:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    return db_siparis


@router.delete("/{siparis_id}")
def siparis_sil(
    siparis_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Bir siparişi pasife alır (soft delete)."""
    success = crud.delete_siparis(db, siparis_id, kullanici_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")
    return {"message": "Sipariş başarıyla pasife alındı", "id": siparis_id}
