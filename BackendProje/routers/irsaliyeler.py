from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import require_role
from models import Kullanici
from services.irsaliye_service import IrsaliyeService
from schemas import IrsaliyeCreate, IrsaliyeUpdate, IrsaliyeResponse

router = APIRouter(prefix="/api/irsaliyeler", tags=["İrsaliyeler"])


@router.get("/", response_model=list[IrsaliyeResponse])
def irsaliyeler_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
):
    return IrsaliyeService.get_irsaliyeler(db, skip=skip, limit=limit, durum=durum, arama=arama)


@router.get("/{irsaliye_id}", response_model=IrsaliyeResponse)
def irsaliye_detay(
    irsaliye_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
):
    return IrsaliyeService.get_irsaliye(db, irsaliye_id)


@router.post("/", response_model=IrsaliyeResponse, status_code=201)
def irsaliye_ekle(
    irsaliye: IrsaliyeCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return IrsaliyeService.create_irsaliye(db, irsaliye, kullanici_id=current_user.id)


@router.put("/{irsaliye_id}", response_model=IrsaliyeResponse)
def irsaliye_guncelle(
    irsaliye_id: int,
    irsaliye_update: IrsaliyeUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return IrsaliyeService.update_irsaliye(db, irsaliye_id, irsaliye_update, kullanici_id=current_user.id)


@router.get("/{irsaliye_id}/yazdir")
def irsaliye_yazdir_verisi(
    irsaliye_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
):
    """İrsaliye yazdırma verisi: irsaliye + sipariş + kalemler (ürün adıyla birlikte)."""
    return IrsaliyeService.get_yazdir_verisi(db, irsaliye_id)
