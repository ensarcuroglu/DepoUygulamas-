from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas import DestekTalebiCreate, DestekTalebiUpdate, DestekTalebiResponse
from models import Kullanici
from auth import get_current_user, require_role
from services.destek_service import DestekService

router = APIRouter(prefix="/api/destek", tags=["Destek Masası"])


@router.get("/", response_model=list[DestekTalebiResponse])
def get_destek_talepleri(
    durum: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Admin tüm talepleri, normal kullanıcı sadece kendi taleplerini görür."""
    return DestekService.get_talepler(db, current_user, skip=skip, limit=limit, durum=durum)


@router.get("/{talep_id}", response_model=DestekTalebiResponse)
def get_destek_talebi(
    talep_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    return DestekService.get_talep(db, talep_id, current_user)


@router.post("/", response_model=DestekTalebiResponse)
def create_destek_talebi(
    talep: DestekTalebiCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    return DestekService.create_talep(db, talep, kullanici_id=current_user.id)


@router.put("/{talep_id}", response_model=DestekTalebiResponse)
def update_destek_talebi(
    talep_id: int,
    talep_update: DestekTalebiUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Sadece admin destek talebinin durumunu ve cevabını güncelleyebilir."""
    return DestekService.update_talep(db, talep_id, talep_update, admin_id=current_user.id)
