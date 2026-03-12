"""Kullanıcı Yönetimi — Service Layer
Tüm business logic (şifre hash, rol kontrolü, duplicate check) burada.
"""
from typing import List
from sqlalchemy.orm import Session

from models import Kullanici
from schemas import KullaniciResponse, KullaniciUpdate
from core.exceptions import NotFoundError, DuplicateError, PermissionDeniedError, BadRequestError
from auth import get_password_hash


class KullaniciService:

    @staticmethod
    def get_kullanicilar(db: Session) -> List[Kullanici]:
        return db.query(Kullanici).order_by(Kullanici.id).all()

    @staticmethod
    def get_kullanici(db: Session, kullanici_id: int) -> Kullanici:
        user = db.query(Kullanici).filter(Kullanici.id == kullanici_id).first()
        if not user:
            raise NotFoundError("Kullanıcı", kullanici_id)
        return user

    @staticmethod
    def update_kullanici(
        db: Session,
        kullanici_id: int,
        data: KullaniciUpdate,
        current_user: Kullanici,
    ) -> Kullanici:
        # Yetki: admin değilse sadece kendi hesabını güncelleyebilir
        if current_user.rol != "admin" and current_user.id != kullanici_id:
            raise PermissionDeniedError(
                "Bu işlem için yönetici yetkisi veya hesap sahibi olmanız gereklidir"
            )

        user = KullaniciService.get_kullanici(db, kullanici_id)

        # Kullanıcı adı değişiyorsa çakışma kontrolü
        if data.kullanici_adi and data.kullanici_adi != user.kullanici_adi:
            existing = db.query(Kullanici).filter(
                Kullanici.kullanici_adi == data.kullanici_adi
            ).first()
            if existing:
                raise DuplicateError("Kullanıcı adı", data.kullanici_adi)
            user.kullanici_adi = data.kullanici_adi

        if data.ad_soyad is not None:
            user.ad_soyad = data.ad_soyad

        if data.rol is not None:
            if current_user.rol != "admin" and data.rol != user.rol:
                raise PermissionDeniedError("Sadece yöneticiler rol değiştirebilir")
            user.rol = data.rol

        if data.sifre:
            user.sifre_hash = get_password_hash(data.sifre)

        for field in ("telefon", "email", "departman", "sicil_no", "kart_numarasi"):
            value = getattr(data, field, None)
            if value is not None:
                setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_kullanici(db: Session, kullanici_id: int, current_user: Kullanici) -> dict:
        if kullanici_id == current_user.id:
            raise BadRequestError("Kendi hesabınızı silemezsiniz")

        user = KullaniciService.get_kullanici(db, kullanici_id)
        db.delete(user)
        db.commit()
        return {"message": "Kullanıcı başarıyla silindi", "id": kullanici_id}
