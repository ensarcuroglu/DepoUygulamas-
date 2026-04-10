from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.entities.zon import Zon
from app.core.repositories.zon_repository import IZonRepository
from app.infrastructure.persistence.mappers import zon_to_entity, zon_to_orm
from models import Zon as ZonORM


class SqlAlchemyZonRepository(IZonRepository):
    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        depo_id: Optional[int] = None,
        tip: Optional[str] = None,
        sadece_aktif: bool = True,
    ) -> List[Zon]:
        query = self._db.query(ZonORM)
        if sadece_aktif:
            query = query.filter(ZonORM.aktif)
        if depo_id is not None:
            query = query.filter(ZonORM.depo_id == depo_id)
        if tip:
            query = query.filter(ZonORM.tip == tip)
        return [zon_to_entity(o) for o in query.order_by(ZonORM.sira.asc(), ZonORM.id.asc()).offset(skip).limit(limit).all()]

    def getir_id_ile(self, zon_id: int) -> Optional[Zon]:
        orm = self._db.query(ZonORM).filter(ZonORM.id == zon_id).first()
        return zon_to_entity(orm) if orm else None

    def getir_kod_ile(self, kod: str) -> Optional[Zon]:
        orm = self._db.query(ZonORM).filter(ZonORM.kod.ilike(kod)).first()
        return zon_to_entity(orm) if orm else None

    def olustur(self, zon: Zon) -> Zon:
        orm = zon_to_orm(zon)
        orm.id = None  # type: ignore[assignment]
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return zon_to_entity(orm)

    def guncelle(self, zon: Zon) -> "Optional[Zon]":
        orm = self._db.query(ZonORM).filter(ZonORM.id == zon.id).first()
        if not orm:
            return None
        orm.depo_id = zon.depo_id
        orm.isim = zon.isim
        orm.tip = zon.tip
        orm.kod = zon.kod
        orm.aciklama = zon.aciklama
        orm.sira = zon.sira
        orm.aktif = zon.aktif
        self._db.commit()
        self._db.refresh(orm)
        return zon_to_entity(orm)

    def sil(self, zon_id: int) -> bool:
        orm = self._db.query(ZonORM).filter(ZonORM.id == zon_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True

