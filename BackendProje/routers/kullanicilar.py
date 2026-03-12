"""Kullanıcılar Router — Kullanıcı Yönetimi"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Kullanici
from auth import get_current_user, require_role
from schemas import KullaniciResponse, KullaniciUpdate
from services.kullanici_service import KullaniciService

router = APIRouter(prefix="/api/kullanicilar", tags=["Kullanıcı Yönetimi"])


@router.get("/", response_model=list[KullaniciResponse])
def kullanicilari_listele(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Tüm kullanıcıları listeler. Sadece admin erişebilir."""
    return KullaniciService.get_kullanicilar(db)


@router.get("/{kullanici_id}", response_model=KullaniciResponse)
def kullanici_detay(
    kullanici_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Belirli bir kullanıcının detaylarını getirir."""
    return KullaniciService.get_kullanici(db, kullanici_id)


@router.put("/{kullanici_id}", response_model=KullaniciResponse)
def kullanici_guncelle(
    kullanici_id: int,
    data: KullaniciUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Kullanıcı bilgilerini günceller (ad, soyad, rol, şifre).
    Admin tüm kullanıcıları; normal kullanıcı yalnızca kendi hesabını güncelleyebilir.
    """
    return KullaniciService.update_kullanici(db, kullanici_id, data, current_user)


@router.delete("/{kullanici_id}")
def kullanici_sil(
    kullanici_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Bir kullanıcıyı siler. Admin kendini silemez."""
    return KullaniciService.delete_kullanici(db, kullanici_id, current_user)
