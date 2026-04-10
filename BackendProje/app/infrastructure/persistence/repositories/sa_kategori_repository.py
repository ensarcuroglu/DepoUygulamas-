from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.entities.kategori import Kategori
from app.core.repositories.kategori_repository import IKategoriRepository
from app.infrastructure.persistence.mappers import kategori_to_entity, kategori_to_orm
from models import Kategori as KategoriORM


class SqlAlchemyKategoriRepository(IKategoriRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Kategori]:
        query = self._db.query(KategoriORM)
        if sadece_aktif:
            query = query.filter(KategoriORM.aktif)
        return [kategori_to_entity(o) for o in query.offset(skip).limit(limit).all()]

    def getir_id_ile(self, kategori_id: int) -> Optional[Kategori]:
        orm = self._db.query(KategoriORM).filter(KategoriORM.id == kategori_id).first()
        return kategori_to_entity(orm) if orm else None

    def olustur(self, kategori: Kategori) -> Kategori:
        orm = kategori_to_orm(kategori)
        orm.id = None  # type: ignore[assignment]
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return kategori_to_entity(orm)

    def guncelle(self, kategori: Kategori) -> "Optional[Kategori]":
        orm = self._db.query(KategoriORM).filter(KategoriORM.id == kategori.id).first()
        if not orm:
            return None
        orm.isim = kategori.isim
        orm.aciklama = kategori.aciklama
        orm.ikon = kategori.ikon
        orm.aktif = kategori.aktif
        self._db.commit()
        self._db.refresh(orm)
        return kategori_to_entity(orm)

    def getir_isim_ile(self, isim: str) -> Optional[Kategori]:
        orm = (
            self._db.query(KategoriORM)
            .filter(KategoriORM.isim.ilike(isim))
            .first()
        )
        return kategori_to_entity(orm) if orm else None

    def sil(self, kategori_id: int) -> bool:
        orm = self._db.query(KategoriORM).filter(KategoriORM.id == kategori_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True
