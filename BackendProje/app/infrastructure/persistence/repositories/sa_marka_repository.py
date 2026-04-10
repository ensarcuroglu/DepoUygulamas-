from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.entities.marka import Marka
from app.core.repositories.marka_repository import IMarkaRepository
from app.infrastructure.persistence.mappers import marka_to_entity, marka_to_orm
from models import Marka as MarkaORM


class SqlAlchemyMarkaRepository(IMarkaRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Marka]:
        query = self._db.query(MarkaORM)
        if sadece_aktif:
            query = query.filter(MarkaORM.aktif)
        orm_list = query.offset(skip).limit(limit).all()
        return [marka_to_entity(o) for o in orm_list]

    def getir_id_ile(self, marka_id: int) -> Optional[Marka]:
        orm = self._db.query(MarkaORM).filter(MarkaORM.id == marka_id).first()
        return marka_to_entity(orm) if orm else None

    def olustur(self, marka: Marka) -> Marka:
        orm = marka_to_orm(marka)
        orm.id = None  # Yeni kayıt
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return marka_to_entity(orm)

    def guncelle(self, marka: Marka) -> Marka:
        orm = self._db.query(MarkaORM).filter(MarkaORM.id == marka.id).first()
        if not orm:
            return None
        orm.isim = marka.isim
        orm.aciklama = marka.aciklama
        orm.aktif = marka.aktif
        self._db.commit()
        self._db.refresh(orm)
        return marka_to_entity(orm)

    def getir_isim_ile(self, isim: str) -> Optional[Marka]:
        orm = (
            self._db.query(MarkaORM)
            .filter(MarkaORM.isim.ilike(isim))
            .first()
        )
        return marka_to_entity(orm) if orm else None

    def sil(self, marka_id: int) -> bool:
        orm = self._db.query(MarkaORM).filter(MarkaORM.id == marka_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True
