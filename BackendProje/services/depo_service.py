"""Depo & Raf İşlemleri — Service Layer"""
from typing import List, Optional
from sqlalchemy.orm import Session
from models import Depo, Raf
from schemas import DepoCreate, DepoUpdate, RafCreate, RafUpdate
from core.exceptions import NotFoundError, DuplicateError
import crud


class DepoService:

    @staticmethod
    def get_depolar(db: Session, skip: int = 0, limit: int = 100) -> List[Depo]:
        return crud.get_depolar(db, skip=skip, limit=limit)

    @staticmethod
    def get_depo(db: Session, depo_id: int) -> Depo:
        d = crud.get_depo(db, depo_id)
        if not d:
            raise NotFoundError("Depo", depo_id)
        return d

    @staticmethod
    def create_depo(db: Session, data: DepoCreate, kullanici_id: int) -> Depo:
        return crud.create_depo(db, data, kullanici_id=kullanici_id)

    @staticmethod
    def update_depo(db: Session, depo_id: int, data: DepoUpdate) -> Depo:
        DepoService.get_depo(db, depo_id)
        return crud.update_depo(db, depo_id, data)

    @staticmethod
    def delete_depo(db: Session, depo_id: int) -> bool:
        DepoService.get_depo(db, depo_id)
        return crud.delete_depo(db, depo_id)


class RafService:

    @staticmethod
    def get_raflar(db: Session, skip: int = 0, limit: int = 500, depo_id: Optional[int] = None) -> List[Raf]:
        return crud.get_raflar(db, skip=skip, limit=limit, depo_id=depo_id)

    @staticmethod
    def get_raf(db: Session, raf_id: int) -> Raf:
        r = crud.get_raf(db, raf_id)
        if not r:
            raise NotFoundError("Raf", raf_id)
        return r

    @staticmethod
    def create_raf(db: Session, data: RafCreate) -> Raf:
        # Bağlı depo varlık kontrolü
        depo = crud.get_depo(db, data.depo_id)
        if not depo:
            raise NotFoundError("Depo", data.depo_id)
        # Aynı depoda mükerrer raf kodu kontrolü
        existing = crud.get_raf_by_kod(db, kod=data.kod)
        if existing and existing.depo_id == data.depo_id:
            raise DuplicateError("Raf kodu", data.kod)
        return crud.create_raf(db, data)

    @staticmethod
    def update_raf(db: Session, raf_id: int, data: RafCreate) -> Raf:
        RafService.get_raf(db, raf_id)
        updated = crud.update_raf(db, raf_id=raf_id, raf=data)
        if not updated:
            raise NotFoundError("Raf", raf_id)
        return updated

    @staticmethod
    def delete_raf(db: Session, raf_id: int) -> bool:
        RafService.get_raf(db, raf_id)
        success = crud.delete_raf(db, raf_id)
        if not success:
            from core.exceptions import BadRequestError
            raise BadRequestError("Raf içi dolu olduğu için silinemez")
        return True
