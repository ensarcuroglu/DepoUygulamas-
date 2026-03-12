from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import Optional

import schemas
from database import get_db
from auth import require_role
from models import Kullanici
from services.depo_service import RafService

router = APIRouter(prefix="/api/raflar", tags=["Raflar"])


@router.post("/", response_model=schemas.RafResponse, status_code=status.HTTP_201_CREATED)
def create_raf(
    raf: schemas.RafCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return RafService.create_raf(db, raf)


@router.get("/", response_model=list[schemas.RafResponse])
def read_raflar(
    skip: int = 0,
    limit: int = 500,
    depo_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
):
    return RafService.get_raflar(db, skip=skip, limit=limit, depo_id=depo_id)


@router.get("/{raf_id}", response_model=schemas.RafResponse)
def read_raf(
    raf_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
):
    return RafService.get_raf(db, raf_id)


@router.put("/{raf_id}", response_model=schemas.RafResponse)
def update_raf(
    raf_id: int,
    raf: schemas.RafCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return RafService.update_raf(db, raf_id, raf)


@router.delete("/{raf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_raf(
    raf_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    RafService.delete_raf(db, raf_id)
    return None
