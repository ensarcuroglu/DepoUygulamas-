from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from database import get_db
from auth import require_role
from models import Kullanici
import crud
from schemas import (
    SevkiyatPlaniCreate, SevkiyatPlaniUpdate, SevkiyatPlaniResponse
)

router = APIRouter(prefix="/api/sevkiyat-planlama", tags=["Sevkiyat Planlama"])


@router.get("/", response_model=list[SevkiyatPlaniResponse])
def sevkiyat_planlari_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    tarih_baslang: Optional[date] = Query(None),
    tarih_bitis: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Sevkiyat planlarını listeler (filtreleme destekli)."""
    return crud.get_sevkiyat_planlari(
        db,
        skip=skip,
        limit=limit,
        durum=durum,
        tarih_baslang=tarih_baslang,
        tarih_bitis=tarih_bitis
    )


@router.get("/{plan_id}", response_model=SevkiyatPlaniResponse)
def sevkiyat_plani_detay(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Belirli bir sevkiyat planının detaylarını getirir."""
    db_plan = crud.get_sevkiyat_plani(db, plan_id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Sevkiyat planı bulunamadı")
    return db_plan


@router.post("/", response_model=SevkiyatPlaniResponse, status_code=201)
def sevkiyat_plani_ekle(
    plan: SevkiyatPlaniCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Yeni bir sevkiyat planı oluşturur."""
    # Sipariş var mı kontrol et
    db_siparis = crud.get_siparis(db, plan.siparis_id)
    if not db_siparis:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")

    return crud.create_sevkiyat_plani(db, plan, kullanici_id=current_user.id)


@router.put("/{plan_id}", response_model=SevkiyatPlaniResponse)
def sevkiyat_plani_guncelle(
    plan_id: int,
    plan_update: SevkiyatPlaniUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Mevcut bir sevkiyat planını günceller/durum değiştirir."""
    db_plan = crud.update_sevkiyat_plani(db, plan_id, plan_update, kullanici_id=current_user.id)
    if not db_plan:
        raise HTTPException(status_code=404, detail="Sevkiyat planı bulunamadı")
    return db_plan


@router.delete("/{plan_id}")
def sevkiyat_plani_sil(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Bir sevkiyat planını siler."""
    success = crud.delete_sevkiyat_plani(db, plan_id, kullanici_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Sevkiyat planı bulunamadı")
    return {"message": "Sevkiyat planı başarıyla silindi", "id": plan_id}
