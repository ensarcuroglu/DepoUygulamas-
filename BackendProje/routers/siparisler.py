from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import require_role
from models import Kullanici
from services.siparis_service import SiparisService
from schemas import SiparisCreate, SiparisUpdate, SiparisResponse, SiparisDetayResponse

router = APIRouter(prefix="/api/siparisler", tags=["Siparişler"])


@router.get("/", response_model=list[SiparisResponse])
def siparisler_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SiparisService.get_siparisler(db, skip=skip, limit=limit, durum=durum, arama=arama)


@router.get("/{siparis_id}", response_model=SiparisDetayResponse)
def siparis_detay(
    siparis_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SiparisService.get_siparis(db, siparis_id)


@router.post("/", response_model=SiparisDetayResponse, status_code=201)
def siparis_ekle(
    siparis: SiparisCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SiparisService.create_siparis(db, siparis, kullanici_id=current_user.id)


@router.put("/{siparis_id}", response_model=SiparisDetayResponse)
def siparis_guncelle(
    siparis_id: int,
    siparis_update: SiparisUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return SiparisService.update_siparis(db, siparis_id, siparis_update, kullanici_id=current_user.id)


@router.delete("/{siparis_id}")
def siparis_sil(
    siparis_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    SiparisService.delete_siparis(db, siparis_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Sipariş başarıyla pasife alındı", "id": siparis_id}
