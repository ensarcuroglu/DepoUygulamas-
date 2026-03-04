from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

import crud
import schemas
import models
from database import get_db

# Router oluştur
router = APIRouter(prefix="/api/tedarikciler", tags=["Tedarikçiler"])

@router.get("/", response_model=List[schemas.Tedarikci])
def tedarikcileri_getir(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Kayıtlı tüm tedarikçileri veritabanından çeker ve listeler.
    """
    tedarikciler = crud.get_tedarikciler(db, skip=skip, limit=limit)
    return tedarikciler


@router.post("/", response_model=schemas.Tedarikci)
def tedarikci_olustur(tedarikci: schemas.TedarikciCreate, db: Session = Depends(get_db)):
    """
    Yeni bir tedarikçi kaydı oluşturur.
    """
    return crud.create_tedarikci(db=db, tedarikci=tedarikci)
