"""Sipariş İşlemleri — Service Layer"""
from typing import List, Optional
from sqlalchemy.orm import Session

from schemas import SiparisCreate, SiparisUpdate
from core.exceptions import NotFoundError
import crud


class SiparisService:

    @staticmethod
    def get_siparisler(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ):
        return crud.get_siparisler(db, skip=skip, limit=limit, durum=durum, arama=arama)

    @staticmethod
    def get_siparis(db: Session, siparis_id: int):
        s = crud.get_siparis(db, siparis_id)
        if not s:
            raise NotFoundError("Sipariş", siparis_id)
        return s

    @staticmethod
    def create_siparis(db: Session, data: SiparisCreate, kullanici_id: int):
        return crud.create_siparis(db, data, kullanici_id=kullanici_id)

    @staticmethod
    def update_siparis(db: Session, siparis_id: int, data: SiparisUpdate, kullanici_id: int):
        SiparisService.get_siparis(db, siparis_id)
        return crud.update_siparis(db, siparis_id, data, kullanici_id=kullanici_id)

    @staticmethod
    def delete_siparis(db: Session, siparis_id: int, kullanici_id: int) -> bool:
        SiparisService.get_siparis(db, siparis_id)
        return crud.delete_siparis(db, siparis_id, kullanici_id=kullanici_id)
