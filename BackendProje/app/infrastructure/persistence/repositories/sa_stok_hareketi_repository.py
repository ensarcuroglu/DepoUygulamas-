from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.core.entities.stok_hareketi import StokHareketi
from app.core.repositories.stok_hareketi_repository import IStokHareketiRepository
from app.infrastructure.persistence.mappers import stok_hareketi_to_entity, stok_hareketi_to_orm
from models import StokHareketi as StokHareketiORM


class SqlAlchemyStokHareketiRepository(IStokHareketiRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        urun_id: Optional[int] = None,
        lot_id: Optional[int] = None,
        hareket_tipi: Optional[str] = None,
    ) -> List[StokHareketi]:
        query = self._db.query(StokHareketiORM).options(
            joinedload(StokHareketiORM.kullanici),
            joinedload(StokHareketiORM.raf),
        ).order_by(StokHareketiORM.tarih.desc())

        if urun_id:
            query = query.filter(StokHareketiORM.urun_id == urun_id)
        if lot_id:
            query = query.filter(StokHareketiORM.lot_id == lot_id)
        if hareket_tipi:
            query = query.filter(StokHareketiORM.hareket_tipi == hareket_tipi)

        return [stok_hareketi_to_entity(o) for o in query.offset(skip).limit(limit).all()]

    def olustur(self, hareket: StokHareketi, auto_commit: bool = True) -> StokHareketi:
        orm = stok_hareketi_to_orm(hareket)
        orm.id = None
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
        self._db.refresh(orm)
        return stok_hareketi_to_entity(orm)
