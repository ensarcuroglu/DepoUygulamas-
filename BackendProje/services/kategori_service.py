"""Kategori İşlemleri — Service Layer"""
from typing import List
from sqlalchemy.orm import Session
from models import Kategori
from schemas import KategoriCreate, KategoriUpdate
from core.exceptions import NotFoundError, DuplicateError
import crud


class KategoriService:

    @staticmethod
    def get_kategoriler(db: Session, skip: int = 0, limit: int = 100) -> List[Kategori]:
        return crud.get_kategoriler(db, skip=skip, limit=limit)

    @staticmethod
    def get_kategori(db: Session, kategori_id: int) -> Kategori:
        k = crud.get_kategori(db, kategori_id)
        if not k:
            raise NotFoundError("Kategori", kategori_id)
        return k

    @staticmethod
    def create_kategori(db: Session, data: KategoriCreate, kullanici_id: int) -> Kategori:
        existing = db.query(Kategori).filter(Kategori.isim == data.isim).first()
        if existing:
            raise DuplicateError("Kategori adı", data.isim)
        return crud.create_kategori(db, data, kullanici_id=kullanici_id)

    @staticmethod
    def update_kategori(db: Session, kategori_id: int, data: KategoriUpdate, kullanici_id: int) -> Kategori:
        KategoriService.get_kategori(db, kategori_id)
        return crud.update_kategori(db, kategori_id, data, kullanici_id=kullanici_id)

    @staticmethod
    def delete_kategori(db: Session, kategori_id: int, kullanici_id: int) -> bool:
        KategoriService.get_kategori(db, kategori_id)
        return crud.delete_kategori(db, kategori_id, kullanici_id=kullanici_id)
