from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from database import get_db
from auth import require_role
from models import Kullanici
from services.sevkiyat_service import SevkiyatService
from schemas import SevkiyatPlaniCreate, SevkiyatPlaniUpdate, SevkiyatPlaniResponse

router = APIRouter(prefix="/api/sevkiyat-planlama", tags=["Sevkiyat Planlama"])


@router.get("/", response_model=list[SevkiyatPlaniResponse])
def sevkiyat_planlari_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    tarih_baslang: Optional[date] = Query(None),
    tarih_bitis: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SevkiyatService.get_planlari(
        db, skip=skip, limit=limit,
        durum=durum, tarih_baslang=tarih_baslang, tarih_bitis=tarih_bitis,
    )


@router.get("/{plan_id}", response_model=SevkiyatPlaniResponse)
def sevkiyat_plani_detay(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SevkiyatService.get_plan(db, plan_id)


@router.post("/", response_model=SevkiyatPlaniResponse, status_code=201)
def sevkiyat_plani_ekle(
    plan: SevkiyatPlaniCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SevkiyatService.create_plan(db, plan, kullanici_id=current_user.id)


@router.put("/{plan_id}", response_model=SevkiyatPlaniResponse)
def sevkiyat_plani_guncelle(
    plan_id: int,
    plan_update: SevkiyatPlaniUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SevkiyatService.update_plan(db, plan_id, plan_update, kullanici_id=current_user.id)


@router.delete("/{plan_id}")
def sevkiyat_plani_sil(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    SevkiyatService.delete_plan(db, plan_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Sevkiyat planı başarıyla silindi", "id": plan_id}
