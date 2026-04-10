from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.entities.depo import Depo
from app.core.repositories.depo_repository import IDepoRepository
from app.infrastructure.persistence.mappers import depo_to_entity, depo_to_orm
from models import Depo as DepoORM


class SqlAlchemyDepoRepository(IDepoRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Depo]:
        query = self._db.query(DepoORM)
        if sadece_aktif:
            query = query.filter(DepoORM.aktif)
        return [depo_to_entity(o) for o in query.offset(skip).limit(limit).all()]

    def getir_id_ile(self, depo_id: int) -> Optional[Depo]:
        orm = self._db.query(DepoORM).filter(DepoORM.id == depo_id).first()
        return depo_to_entity(orm) if orm else None

    def olustur(self, depo: Depo) -> Depo:
        orm = depo_to_orm(depo)
        orm.id = None  # type: ignore[assignment]
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return depo_to_entity(orm)

    def guncelle(self, depo: Depo) -> "Optional[Depo]":
        orm = self._db.query(DepoORM).filter(DepoORM.id == depo.id).first()
        if not orm:
            return None
        orm.isim = depo.isim
        orm.adres = depo.adres
        orm.aciklama = depo.aciklama
        orm.aktif = depo.aktif
        self._db.commit()
        self._db.refresh(orm)
        return depo_to_entity(orm)

    def sil(self, depo_id: int) -> bool:
        orm = self._db.query(DepoORM).filter(DepoORM.id == depo_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True
