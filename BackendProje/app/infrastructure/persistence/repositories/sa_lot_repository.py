from typing import List, Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session, joinedload

from app.core.entities.lot import Lot
from app.core.repositories.lot_repository import ILotRepository
from app.infrastructure.persistence.mappers import lot_to_entity, lot_to_orm
from models import Lot as LotORM


class SqlAlchemyLotRepository(ILotRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        urun_id: Optional[int] = None, sadece_aktif: bool = True,
    ) -> List[Lot]:
        query = self._db.query(LotORM).options(joinedload(LotORM.urun))
        if sadece_aktif:
            query = query.filter(LotORM.aktif)
        if urun_id:
            query = query.filter(LotORM.urun_id == urun_id)
        orm_list = query.order_by(LotORM.olusturma_tarihi.desc()).offset(skip).limit(limit).all()
        return [lot_to_entity(o) for o in orm_list]

    def getir_id_ile(self, lot_id: int) -> Optional[Lot]:
        orm = self._db.query(LotORM).options(
            joinedload(LotORM.urun),
            joinedload(LotORM.paletler),
        ).filter(LotORM.id == lot_id).first()
        return lot_to_entity(orm) if orm else None

    def getir_lot_no_ile(self, lot_no: str) -> Optional[Lot]:
        orm = self._db.query(LotORM).options(
            joinedload(LotORM.urun),
            joinedload(LotORM.paletler),
        ).filter(LotORM.lot_no == lot_no).first()
        return lot_to_entity(orm) if orm else None

    def olustur(self, lot: Lot, auto_commit: bool = True) -> Lot:
        orm = lot_to_orm(lot)
        orm.id = None  # type: ignore[assignment]
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
        self._db.refresh(orm)
        return lot_to_entity(orm)

    def guncelle(self, lot: Lot, auto_commit: bool = True) -> "Optional[Lot]":
        orm = self._db.query(LotORM).filter(LotORM.id == lot.id).first()
        if not orm:
            return None
        orm.urun_id = lot.urun_id
        orm.lot_no = lot.lot_no
        orm.parti_no = lot.parti_no
        orm.uretim_tarihi = lot.uretim_tarihi
        orm.son_kullanma_tarihi = lot.son_kullanma_tarihi
        orm.aciklama = lot.aciklama
        orm.aktif = lot.aktif
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
        self._db.refresh(orm)
        return lot_to_entity(orm)

    def sil(self, lot_id: int) -> bool:
        orm = self._db.query(LotORM).filter(LotORM.id == lot_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True

    def getir_skt_yaklasan(self, gun: int = 30) -> List[Lot]:
        sinir_tarih = date.today() + timedelta(days=gun)
        orm_list = self._db.query(LotORM).options(
            joinedload(LotORM.urun),
        ).filter(
            LotORM.aktif,
            LotORM.son_kullanma_tarihi is not None,
            LotORM.son_kullanma_tarihi <= sinir_tarih,
        ).order_by(LotORM.son_kullanma_tarihi.asc()).all()
        return [lot_to_entity(o) for o in orm_list]
