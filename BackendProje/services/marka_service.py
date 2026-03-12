"""Marka İşlemleri — Service Layer"""
from typing import List
from sqlalchemy.orm import Session
from models import Marka
from schemas import MarkaCreate, MarkaUpdate
from core.exceptions import NotFoundError, DuplicateError
import crud


class MarkaService:

    @staticmethod
    def get_markalar(db: Session, skip: int = 0, limit: int = 100) -> List[Marka]:
        return crud.get_markalar(db, skip=skip, limit=limit)

    @staticmethod
    def get_marka(db: Session, marka_id: int) -> Marka:
        m = crud.get_marka(db, marka_id)
        if not m:
            raise NotFoundError("Marka", marka_id)
        return m

    @staticmethod
    def create_marka(db: Session, data: MarkaCreate) -> Marka:
        existing = db.query(Marka).filter(Marka.isim == data.isim).first()
        if existing:
            raise DuplicateError("Marka adı", data.isim)
        return crud.create_marka(db, data)

    @staticmethod
    def update_marka(db: Session, marka_id: int, data: MarkaUpdate) -> Marka:
        MarkaService.get_marka(db, marka_id)
        return crud.update_marka(db, marka_id, data)

    @staticmethod
    def delete_marka(db: Session, marka_id: int) -> bool:
        MarkaService.get_marka(db, marka_id)
        return crud.delete_marka(db, marka_id)
