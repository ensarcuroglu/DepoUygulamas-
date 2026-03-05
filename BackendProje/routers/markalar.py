from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_user
from models import Kullanici
import crud
from schemas import MarkaCreate, MarkaUpdate, MarkaResponse

router = APIRouter(prefix="/api/markalar", tags=["Markalar"])


@router.get("/", response_model=list[MarkaResponse])
def markalari_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Tüm markaları listeler."""
    return crud.get_markalar(db, skip=skip, limit=limit)


@router.get("/{marka_id}", response_model=MarkaResponse)
def marka_detay(
    marka_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Belirli bir markanın detaylarını getirir."""
    db_marka = crud.get_marka(db, marka_id)
    if not db_marka:
        raise HTTPException(status_code=404, detail="Marka bulunamadı")
    return db_marka


@router.post("/", response_model=MarkaResponse, status_code=201)
def marka_ekle(
    marka: MarkaCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Yeni bir marka ekler."""
    return crud.create_marka(db, marka)


@router.put("/{marka_id}", response_model=MarkaResponse)
def marka_guncelle(
    marka_id: int,
    marka: MarkaUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Mevcut bir markayı günceller."""
    db_marka = crud.update_marka(db, marka_id, marka)
    if not db_marka:
        raise HTTPException(status_code=404, detail="Marka bulunamadı")
    return db_marka


@router.delete("/{marka_id}")
def marka_sil(
    marka_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Bir markayı pasife alır (soft delete)."""
    success = crud.delete_marka(db, marka_id)
    if not success:
        raise HTTPException(status_code=404, detail="Marka bulunamadı")
    return {"message": "Marka başarıyla pasife alındı", "id": marka_id}
