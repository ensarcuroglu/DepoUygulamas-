"""
Kullanıcılar Router — Kullanıcı Yönetimi (Sadece Admin)
Listeleme, Detay, Güncelleme, Silme
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from models import Kullanici
from auth import get_current_user, get_password_hash
from schemas import KullaniciResponse, KullaniciUpdate

router = APIRouter(prefix="/api/kullanicilar", tags=["Kullanıcı Yönetimi"])


def require_admin(current_user: Kullanici = Depends(get_current_user)) -> Kullanici:
    """Admin yetkisi zorunlu kılan dependency."""
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkisi gereklidir."
        )
    return current_user


@router.get("/", response_model=list[KullaniciResponse])
def kullanicilari_listele(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_admin)
):
    """Tüm kullanıcıları listeler. Sadece admin erişebilir."""
    return db.query(Kullanici).order_by(Kullanici.id).all()


@router.get("/{kullanici_id}", response_model=KullaniciResponse)
def kullanici_detay(
    kullanici_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_admin)
):
    """Belirli bir kullanıcının detaylarını getirir."""
    user = db.query(Kullanici).filter(Kullanici.id == kullanici_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")
    return user


@router.put("/{kullanici_id}", response_model=KullaniciResponse)
def kullanici_guncelle(
    kullanici_id: int,
    data: KullaniciUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Bir kullanıcının bilgilerini günceller (ad, soyad, rol, şifre)."""
    # 1. Yetki Kontrolü: Admin değilse ve kendi hesabını güncellemiyorsa RET
    if current_user.rol != "admin" and current_user.id != kullanici_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlem için yönetici yetkisi veya hesap sahibi olmanız gereklidir."
        )

    user = db.query(Kullanici).filter(Kullanici.id == kullanici_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    # Kullanıcı adı değişiyorsa çakışma kontrolü
    if data.kullanici_adi and data.kullanici_adi != user.kullanici_adi:
        existing = db.query(Kullanici).filter(
            Kullanici.kullanici_adi == data.kullanici_adi
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Bu kullanıcı adı zaten kullanımda."
            )
        user.kullanici_adi = data.kullanici_adi

    if data.ad_soyad is not None:
        user.ad_soyad = data.ad_soyad
    if data.rol is not None:
        if current_user.rol != "admin" and data.rol != user.rol:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sadece yöneticiler rol değiştirebilir."
            )
        user.rol = data.rol
    if data.sifre:
        user.sifre_hash = get_password_hash(data.sifre)
    if data.telefon is not None:
        user.telefon = data.telefon
    if data.email is not None:
        user.email = data.email
    if data.departman is not None:
        user.departman = data.departman
    if data.sicil_no is not None:
        user.sicil_no = data.sicil_no
    if data.kart_numarasi is not None:
        user.kart_numarasi = data.kart_numarasi

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{kullanici_id}")
def kullanici_sil(
    kullanici_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_admin)
):
    """Bir kullanıcıyı siler. Admin kendini silemez."""
    if kullanici_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="Kendi hesabınızı silemezsiniz."
        )

    user = db.query(Kullanici).filter(Kullanici.id == kullanici_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı")

    db.delete(user)
    db.commit()
    return {"message": "Kullanıcı başarıyla silindi", "id": kullanici_id}
