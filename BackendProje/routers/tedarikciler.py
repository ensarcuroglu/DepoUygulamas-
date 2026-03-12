from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
from database import get_db
from auth import require_role
from models import Kullanici
from services.tedarikci_service import TedarikciService

router = APIRouter(prefix="/api/tedarikciler", tags=["Tedarikçiler"])


@router.get("/", response_model=list[schemas.TedarikciResponse])
def tedarikcileri_getir(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return TedarikciService.get_tedarikciler(db, skip=skip, limit=limit)


@router.get("/{tedarikci_id}", response_model=schemas.TedarikciResponse)
def tedarikci_detay(
    tedarikci_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return TedarikciService.get_tedarikci(db, tedarikci_id)


@router.post("/", response_model=schemas.TedarikciResponse, status_code=201)
def tedarikci_olustur(
    tedarikci: schemas.TedarikciCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return TedarikciService.create_tedarikci(db, tedarikci)


@router.put("/{tedarikci_id}", response_model=schemas.TedarikciResponse)
def tedarikci_guncelle(
    tedarikci_id: int,
    tedarikci: schemas.TedarikciUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return TedarikciService.update_tedarikci(db, tedarikci_id, tedarikci)


@router.delete("/{tedarikci_id}")
def tedarikci_sil(
    tedarikci_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    TedarikciService.delete_tedarikci(db, tedarikci_id)
    return {"success": True, "message": "Tedarikçi başarıyla pasife alındı", "id": tedarikci_id}
