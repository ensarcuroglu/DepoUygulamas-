from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date

from database import get_db
from auth import require_role
from models import Kullanici
import crud
from schemas import (
    RaporSablonuCreate, RaporSablonuUpdate, RaporSablonuResponse,
    RaporLoguResponse,
    RaporScheduleCreate, RaporScheduleUpdate, RaporScheduleResponse
)

router = APIRouter(prefix="/api/raporlar", tags=["Raporlar"])


# ========================
# RAPOR ŞABLONLARI
# ========================

@router.get("/sablonlar", response_model=list[RaporSablonuResponse])
def rapor_sablonlarini_listele(
    skip: int = 0,
    limit: int = 100,
    tur: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Tüm rapor şablonlarını listeler"""
    return crud.get_rapor_sablonlari(db, skip=skip, limit=limit, tur=tur)


@router.get("/sablonlar/{sablon_id}", response_model=RaporSablonuResponse)
def rapor_sablonunu_getir(
    sablon_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Belirli bir rapor şablonunu getirir"""
    db_sablon = crud.get_rapor_sablonu(db, sablon_id)
    if not db_sablon:
        raise HTTPException(status_code=404, detail="Rapor şablonu bulunamadı")
    return db_sablon


@router.post("/sablonlar", response_model=RaporSablonuResponse, status_code=201)
def rapor_sablonu_ekle(
    sablon: RaporSablonuCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni bir rapor şablonu oluşturur"""
    return crud.create_rapor_sablonu(db, sablon, kullanici_id=current_user.id)


@router.put("/sablonlar/{sablon_id}", response_model=RaporSablonuResponse)
def rapor_sablonunu_guncelle(
    sablon_id: int,
    sablon_update: RaporSablonuUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Rapor şablonunu günceller"""
    db_sablon = crud.update_rapor_sablonu(db, sablon_id, sablon_update, kullanici_id=current_user.id)
    if not db_sablon:
        raise HTTPException(status_code=404, detail="Rapor şablonu bulunamadı")
    return db_sablon


@router.delete("/sablonlar/{sablon_id}")
def rapor_sablonunu_sil(
    sablon_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Rapor şablonunu pasife alır"""
    success = crud.delete_rapor_sablonu(db, sablon_id, kullanici_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Rapor şablonu bulunamadı")
    return {"message": "Rapor şablonu başarıyla pasife alındı", "id": sablon_id}


# ========================
# RAPOR VERİLERİ
# ========================

@router.get("/stok/veriler")
def stok_raporu_verisi(
    urun_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Stok raporu için veri döndür"""
    return {"veri": crud.get_stok_raporu_verileri(db, urun_id=urun_id)}


@router.get("/siparis/veriler")
def siparis_raporu_verisi(
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Sipariş raporu için veri döndür"""
    return {"veri": crud.get_siparis_raporu_verileri(db, baslang_tarihi, bitis_tarihi)}


@router.get("/hareket/veriler")
def hareket_raporu_verisi(
    baslang_tarihi: Optional[date] = Query(None),
    bitis_tarihi: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Stok hareketi raporu için veri döndür"""
    return {"veri": crud.get_hareket_raporu_verileri(db, baslang_tarihi, bitis_tarihi)}


# ========================
# RAPOR LOGLARI
# ========================

@router.get("/log", response_model=list[RaporLoguResponse])
def rapor_loglari_listele(
    skip: int = 0,
    limit: int = 100,
    sablon_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Rapor oluşturma geçmişini listeler"""
    return crud.get_rapor_loglari(db, skip=skip, limit=limit, sablon_id=sablon_id)


# ========================
# RAPOR ZAMANLAMASI
# ========================

@router.get("/schedule", response_model=list[RaporScheduleResponse])
def rapor_schedules_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı raporları listeler"""
    return crud.get_rapor_schedules(db, skip=skip, limit=limit)


@router.get("/schedule/{schedule_id}", response_model=RaporScheduleResponse)
def rapor_schedule_detay(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı rapor detayını getirir"""
    db_schedule = crud.get_rapor_schedule(db, schedule_id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Zamanlı rapor bulunamadı")
    return db_schedule


@router.post("/schedule", response_model=RaporScheduleResponse, status_code=201)
def rapor_schedule_ekle(
    schedule: RaporScheduleCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni zamanlı rapor oluşturur"""
    return crud.create_rapor_schedule(db, schedule, kullanici_id=current_user.id)


@router.put("/schedule/{schedule_id}", response_model=RaporScheduleResponse)
def rapor_schedule_guncelle(
    schedule_id: int,
    schedule_update: RaporScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı raporu günceller"""
    db_schedule = crud.update_rapor_schedule(db, schedule_id, schedule_update, kullanici_id=current_user.id)
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Zamanlı rapor bulunamadı")
    return db_schedule


@router.delete("/schedule/{schedule_id}")
def rapor_schedule_sil(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Zamanlı raporu siler"""
    success = crud.delete_rapor_schedule(db, schedule_id, kullanici_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Zamanlı rapor bulunamadı")
    return {"message": "Zamanlı rapor başarıyla silindi", "id": schedule_id}
