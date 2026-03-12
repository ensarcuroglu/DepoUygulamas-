"""Sevkiyat Planlama — Service Layer"""
from typing import Optional
from datetime import date
from sqlalchemy.orm import Session

from schemas import SevkiyatPlaniCreate, SevkiyatPlaniUpdate
from core.exceptions import NotFoundError
import crud


class SevkiyatService:

    @staticmethod
    def get_planlari(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        tarih_baslang: Optional[date] = None,
        tarih_bitis: Optional[date] = None,
    ):
        return crud.get_sevkiyat_planlari(
            db, skip=skip, limit=limit,
            durum=durum, tarih_baslang=tarih_baslang, tarih_bitis=tarih_bitis,
        )

    @staticmethod
    def get_plan(db: Session, plan_id: int):
        p = crud.get_sevkiyat_plani(db, plan_id)
        if not p:
            raise NotFoundError("Sevkiyat planı", plan_id)
        return p

    @staticmethod
    def create_plan(db: Session, data: SevkiyatPlaniCreate, kullanici_id: int):
        siparis = crud.get_siparis(db, data.siparis_id)
        if not siparis:
            raise NotFoundError("Sipariş", data.siparis_id)
        return crud.create_sevkiyat_plani(db, data, kullanici_id=kullanici_id)

    @staticmethod
    def update_plan(db: Session, plan_id: int, data: SevkiyatPlaniUpdate, kullanici_id: int):
        SevkiyatService.get_plan(db, plan_id)
        return crud.update_sevkiyat_plani(db, plan_id, data, kullanici_id=kullanici_id)

    @staticmethod
    def delete_plan(db: Session, plan_id: int, kullanici_id: int) -> bool:
        SevkiyatService.get_plan(db, plan_id)
        return crud.delete_sevkiyat_plani(db, plan_id, kullanici_id=kullanici_id)
