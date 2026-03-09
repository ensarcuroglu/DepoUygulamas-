from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import crud
from schemas import DestekTalebiCreate, DestekTalebiUpdate, DestekTalebiResponse
from models import Kullanici
from auth import get_current_user, require_role

router = APIRouter(prefix="/api/destek", tags=["Destek Masası"])


@router.get("/", response_model=List[DestekTalebiResponse])
def get_destek_talepleri(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
    durum: str = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Destek taleplerini listeler.
    Admin yetkisine sahipse tüm talepleri (istenirse duruma göre filtreli),
    değilse sadece kendi açtığı talepleri görür.
    """
    if current_user.rol == "admin":
        talepler = crud.get_destek_talepleri(db, skip=skip, limit=limit, durum=durum)
    else:
        talepler = crud.get_destek_talepleri(db, skip=skip, limit=limit, kullanici_id=current_user.id, durum=durum)
    return talepler


@router.get("/{talep_id}", response_model=DestekTalebiResponse)
def get_destek_talebi(
    talep_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Belirli bir destek talebinin detayını getirir.
    Normal kullanıcı sadece kendine ait olanı, admin ise hepsini görebilir.
    """
    talep = crud.get_destek_talebi(db, talep_id=talep_id)
    if not talep:
        raise HTTPException(status_code=404, detail="Destek talebi bulunamadı.")
    
    if current_user.rol != "admin" and talep.kullanici_id != current_user.id:
        raise HTTPException(status_code=403, detail="Bu talebi görüntüleme yetkiniz yok.")
        
    return talep


@router.post("/", response_model=DestekTalebiResponse)
def create_destek_talebi(
    talep: DestekTalebiCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Kullanıcı tarafından yeni bir destek talebi (bilet) oluşturulur.
    """
    yeni_talep = crud.create_destek_talebi(db, talep=talep, kullanici_id=current_user.id)
    return yeni_talep


@router.put("/{talep_id}", response_model=DestekTalebiResponse)
def update_destek_talebi(
    talep_id: int,
    talep_update: DestekTalebiUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """
    Sadece 'admin' rolündeki yetkililer destek talebinin durumunu ve cevabını güncelleyebilir.
    """
    guncellenen_talep = crud.update_destek_talebi(db, talep_id=talep_id, talep_update=talep_update, admin_id=current_user.id)
    if not guncellenen_talep:
        raise HTTPException(status_code=404, detail="Destek talebi bulunamadı veya güncellenemedi.")
        
    return guncellenen_talep
