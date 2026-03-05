from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import schemas, crud
from database import get_db
from routers.auth import get_current_user

router = APIRouter(
    prefix="/raflar",
    tags=["Raflar"],
    dependencies=[Depends(get_current_user)]
)

@router.post("/", response_model=schemas.RafResponse, status_code=status.HTTP_201_CREATED)
def create_raf(raf: schemas.RafCreate, db: Session = Depends(get_db)):
    # Check if depo exists
    db_depo = crud.get_depo(db, depo_id=raf.depo_id)
    if not db_depo:
        raise HTTPException(status_code=404, detail="Bağlı depo bulunamadı")
    
    # Optional: check if raf code already exists in that depo
    db_raf = crud.get_raf_by_kod(db, kod=raf.kod)
    if db_raf and db_raf.depo_id == raf.depo_id:
        raise HTTPException(status_code=400, detail="Bu raf kodu bu depoda zaten mevcut")
        
    return crud.create_raf(db=db, raf=raf)

@router.get("/", response_model=List[schemas.RafResponse])
def read_raflar(skip: int = 0, limit: int = 100, depo_id: int = None, db: Session = Depends(get_db)):
    # Note: crud.get_raflar doesn't currently support depo_id filtering in the main crud.py
    # But for a simple implementation we'll just return all active raflar.
    # In a full app, you should add depo_id support to crud.get_raflar
    raflar = crud.get_raflar(db, skip=skip, limit=limit)
    if depo_id:
        raflar = [r for r in raflar if r.depo_id == depo_id]
    return raflar

@router.get("/{raf_id}", response_model=schemas.RafResponse)
def read_raf(raf_id: int, db: Session = Depends(get_db)):
    db_raf = crud.get_raf(db, raf_id=raf_id)
    if db_raf is None:
        raise HTTPException(status_code=404, detail="Raf bulunamadı")
    return db_raf

@router.put("/{raf_id}", response_model=schemas.RafResponse)
def update_raf(raf_id: int, raf: schemas.RafCreate, db: Session = Depends(get_db)):
    db_raf = crud.update_raf(db, raf_id=raf_id, raf=raf)
    if db_raf is None:
        raise HTTPException(status_code=404, detail="Raf bulunamadı")
    return db_raf

@router.delete("/{raf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_raf(raf_id: int, db: Session = Depends(get_db)):
    success = crud.delete_raf(db, raf_id=raf_id)
    if not success:
        raise HTTPException(status_code=404, detail="Raf bulunamadı VEYA içi dolu olduğu için silinemez")
    return None
