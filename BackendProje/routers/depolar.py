from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from auth import require_role
from models import Depo, Kullanici
import crud
from schemas import DepoCreate, DepoUpdate, DepoResponse

router = APIRouter(
    prefix="/api/depolar",
    tags=["Depolar"],
    dependencies=[Depends(require_role("admin", "lojistik"))]
)

# Tüm endpoint'ler sadece admin ve lojistik erişimlidir


@router.get("/", response_model=list[DepoResponse])
def depolari_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Tüm depoları listeler."""
    return crud.get_depolar(db, skip=skip, limit=limit)


@router.get("/{depo_id}", response_model=DepoResponse)
def depo_detay(
    depo_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Belirli bir deponun detaylarını getirir."""
    db_depo = crud.get_depo(db, depo_id)
    if not db_depo:
        raise HTTPException(status_code=404, detail="Depo bulunamadı")
    return db_depo


@router.post("/", response_model=DepoResponse, status_code=201)
def depo_ekle(
    depo: DepoCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Yeni bir depo ekler."""
    return crud.create_depo(db, depo, kullanici_id=current_user.id)


@router.put("/{depo_id}", response_model=DepoResponse)
def depo_guncelle(
    depo_id: int,
    depo: DepoUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Mevcut bir depoyu günceller."""
    db_depo = crud.update_depo(db, depo_id, depo)
    if not db_depo:
        raise HTTPException(status_code=404, detail="Depo bulunamadı")
    return db_depo


@router.delete("/{depo_id}")
def depo_sil(
    depo_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Bir depoyu pasife alır (soft delete)."""
    success = crud.delete_depo(db, depo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Depo bulunamadı")
    return {"message": "Depo başarıyla pasife alındı", "id": depo_id}
