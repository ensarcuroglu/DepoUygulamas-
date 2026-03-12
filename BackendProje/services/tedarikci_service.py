"""Tedarikçi İşlemleri — Service Layer"""
from typing import List
from sqlalchemy.orm import Session
from schemas import TedarikciCreate, TedarikciUpdate
from core.exceptions import NotFoundError
import crud


class TedarikciService:

    @staticmethod
    def get_tedarikciler(db: Session, skip: int = 0, limit: int = 100):
        return crud.get_tedarikciler(db, skip=skip, limit=limit)

    @staticmethod
    def get_tedarikci(db: Session, tedarikci_id: int):
        t = crud.get_tedarikci(db, tedarikci_id)
        if not t:
            raise NotFoundError("Tedarikçi", tedarikci_id)
        return t

    @staticmethod
    def create_tedarikci(db: Session, data: TedarikciCreate):
        return crud.create_tedarikci(db, data)

    @staticmethod
    def update_tedarikci(db: Session, tedarikci_id: int, data: TedarikciUpdate):
        TedarikciService.get_tedarikci(db, tedarikci_id)
        return crud.update_tedarikci(db, tedarikci_id, data)

    @staticmethod
    def delete_tedarikci(db: Session, tedarikci_id: int) -> bool:
        TedarikciService.get_tedarikci(db, tedarikci_id)
        return crud.delete_tedarikci(db, tedarikci_id)
