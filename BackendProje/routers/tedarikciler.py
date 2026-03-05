from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db
from auth import get_current_user
from models import Kullanici

router = APIRouter(prefix="/api/tedarikciler", tags=["Tedarikçiler"])


@router.get("/", response_model=list[schemas.TedarikciResponse])
def tedarikcileri_getir(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Kayıtlı tüm tedarikçileri listeler."""
    return crud.get_tedarikciler(db, skip=skip, limit=limit)


@router.get("/{tedarikci_id}", response_model=schemas.TedarikciResponse)
def tedarikci_detay(
    tedarikci_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Belirli bir tedarikçinin detaylarını getirir."""
    db_tedarikci = crud.get_tedarikci(db, tedarikci_id)
    if not db_tedarikci:
        raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı")
    return db_tedarikci


@router.post("/", response_model=schemas.TedarikciResponse, status_code=201)
def tedarikci_olustur(
    tedarikci: schemas.TedarikciCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Yeni bir tedarikçi kaydı oluşturur."""
    return crud.create_tedarikci(db=db, tedarikci=tedarikci)


@router.put("/{tedarikci_id}", response_model=schemas.TedarikciResponse)
def tedarikci_guncelle(
    tedarikci_id: int,
    tedarikci: schemas.TedarikciUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Mevcut bir tedarikçiyi günceller."""
    db_tedarikci = crud.update_tedarikci(db, tedarikci_id, tedarikci)
    if not db_tedarikci:
        raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı")
    return db_tedarikci


@router.delete("/{tedarikci_id}")
def tedarikci_sil(
    tedarikci_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Bir tedarikçiyi pasife alır (soft delete)."""
    success = crud.delete_tedarikci(db, tedarikci_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tedarikçi bulunamadı")
    return {"message": "Tedarikçi başarıyla pasife alındı", "id": tedarikci_id}
