from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.entities.raf import Raf
from app.core.repositories.raf_repository import IRafRepository
from app.infrastructure.persistence.mappers import raf_to_entity, raf_to_orm
from models import Raf as RafORM


class SqlAlchemyRafRepository(IRafRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        depo_id: Optional[int] = None,
        zon_id: Optional[int] = None,
        sadece_aktif: bool = True,
    ) -> List[Raf]:
        query = self._db.query(RafORM)
        if sadece_aktif:
            query = query.filter(RafORM.aktif == True)
        if depo_id:
            query = query.filter(RafORM.depo_id == depo_id)
        if zon_id:
            query = query.filter(RafORM.zon_id == zon_id)
        return [raf_to_entity(o) for o in query.offset(skip).limit(limit).all()]

    def getir_id_ile(self, raf_id: int) -> Optional[Raf]:
        orm = self._db.query(RafORM).filter(RafORM.id == raf_id).first()
        return raf_to_entity(orm) if orm else None

    def olustur(self, raf: Raf) -> Raf:
        orm = raf_to_orm(raf)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return raf_to_entity(orm)

    def guncelle(self, raf: Raf) -> Raf:
        orm = self._db.query(RafORM).filter(RafORM.id == raf.id).first()
        if not orm:
            return None
        orm.depo_id = raf.depo_id
        orm.zon_id = raf.zon_id
        orm.kod = raf.kod
        orm.bolge = raf.bolge
        orm.kapasite = raf.kapasite
        orm.max_agirlik_kg = raf.max_agirlik_kg
        orm.koridor = raf.koridor
        orm.kat = raf.kat
        orm.goz = raf.goz
        orm.aktif = raf.aktif
        self._db.commit()
        self._db.refresh(orm)
        return raf_to_entity(orm)

    def getir_kod_ile(self, kod: str, depo_id: int) -> Optional[Raf]:
        orm = (
            self._db.query(RafORM)
            .filter(RafORM.depo_id == depo_id, RafORM.kod.ilike(kod))
            .first()
        )
        return raf_to_entity(orm) if orm else None

    def getir_staging_raf(self, depo_id: int) -> Optional[Raf]:
        orm = (
            self._db.query(RafORM)
            .filter(RafORM.depo_id == depo_id, RafORM.is_staging == True)  # noqa: E712
            .first()
        )
        return raf_to_entity(orm) if orm else None

    def sil(self, raf_id: int) -> bool:
        orm = self._db.query(RafORM).filter(RafORM.id == raf_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True
