"""Destek Masası İşlemleri — Service Layer"""
from typing import List, Optional
from sqlalchemy.orm import Session

from models import Kullanici
from schemas import DestekTalebiCreate, DestekTalebiUpdate
from core.exceptions import NotFoundError, PermissionDeniedError
import crud


class DestekService:

    @staticmethod
    def get_talepler(
        db: Session,
        current_user: Kullanici,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
    ):
        """Admin tüm talepleri, normal kullanıcı sadece kendinkini görür."""
        if current_user.rol == "admin":
            return crud.get_destek_talepleri(db, skip=skip, limit=limit, durum=durum)
        return crud.get_destek_talepleri(
            db, skip=skip, limit=limit,
            kullanici_id=current_user.id, durum=durum,
        )

    @staticmethod
    def get_talep(db: Session, talep_id: int, current_user: Kullanici):
        """Admin her talebi görebilir; normal kullanıcı sadece kendinkini."""
        talep = crud.get_destek_talebi(db, talep_id=talep_id)
        if not talep:
            raise NotFoundError("Destek talebi", talep_id)
        if current_user.rol != "admin" and talep.kullanici_id != current_user.id:
            raise PermissionDeniedError("Bu talebi görüntüleme yetkiniz yok")
        return talep

    @staticmethod
    def create_talep(db: Session, data: DestekTalebiCreate, kullanici_id: int):
        return crud.create_destek_talebi(db, talep=data, kullanici_id=kullanici_id)

    @staticmethod
    def update_talep(db: Session, talep_id: int, data: DestekTalebiUpdate, admin_id: int):
        guncellenen = crud.update_destek_talebi(
            db, talep_id=talep_id, talep_update=data, admin_id=admin_id
        )
        if not guncellenen:
            raise NotFoundError("Destek talebi", talep_id)
        return guncellenen
