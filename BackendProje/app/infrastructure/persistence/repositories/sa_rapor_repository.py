from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.core.entities.rapor import RaporSablonu, RaporLogu, RaporSchedule
from app.core.repositories.rapor_repository import (
    IRaporSablonuRepository, IRaporLoguRepository, IRaporScheduleRepository,
)
from app.infrastructure.persistence.mappers import (
    rapor_sablonu_to_entity, rapor_sablonu_to_orm,
    rapor_logu_to_entity, rapor_logu_to_orm,
    rapor_schedule_to_entity, rapor_schedule_to_orm,
)
from models import (
    RaporSablonu as RaporSablonuORM,
    RaporLogu as RaporLoguORM,
    RaporSchedule as RaporScheduleORM,
)


# ════════════════════════════════════════════
# RAPOR ŞABLONU
# ════════════════════════════════════════════

class SqlAlchemyRaporSablonuRepository(IRaporSablonuRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        tur: Optional[str] = None, is_aktif: bool = True,
    ) -> List[RaporSablonu]:
        query = self._db.query(RaporSablonuORM)
        if is_aktif:
            query = query.filter(RaporSablonuORM.is_aktif == True)
        if tur:
            query = query.filter(RaporSablonuORM.tur == tur)
        orm_list = query.order_by(RaporSablonuORM.ad).offset(skip).limit(limit).all()
        return [rapor_sablonu_to_entity(o) for o in orm_list]

    def getir_id_ile(self, sablon_id: int) -> Optional[RaporSablonu]:
        orm = self._db.query(RaporSablonuORM).filter(RaporSablonuORM.id == sablon_id).first()
        return rapor_sablonu_to_entity(orm) if orm else None

    def olustur(self, sablon: RaporSablonu) -> RaporSablonu:
        orm = rapor_sablonu_to_orm(sablon)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return rapor_sablonu_to_entity(orm)

    def guncelle(self, sablon: RaporSablonu) -> RaporSablonu:
        orm = self._db.query(RaporSablonuORM).filter(RaporSablonuORM.id == sablon.id).first()
        if not orm:
            return None
        orm.ad = sablon.ad
        orm.tur = sablon.tur
        orm.aciklama = sablon.aciklama
        orm.config = sablon.config
        orm.is_aktif = sablon.is_aktif
        orm.guncelleme_tarihi = sablon.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return rapor_sablonu_to_entity(orm)

    def sil(self, sablon_id: int) -> bool:
        orm = self._db.query(RaporSablonuORM).filter(RaporSablonuORM.id == sablon_id).first()
        if not orm:
            return False
        orm.is_aktif = False
        self._db.commit()
        return True


# ════════════════════════════════════════════
# RAPOR LOGU
# ════════════════════════════════════════════

class SqlAlchemyRaporLoguRepository(IRaporLoguRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        sablon_id: Optional[int] = None,
    ) -> List[RaporLogu]:
        query = self._db.query(RaporLoguORM).options(
            joinedload(RaporLoguORM.sablon),
        )
        if sablon_id:
            query = query.filter(RaporLoguORM.sablon_id == sablon_id)
        orm_list = query.order_by(
            RaporLoguORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [rapor_logu_to_entity(o) for o in orm_list]

    def olustur(self, log: RaporLogu) -> RaporLogu:
        orm = rapor_logu_to_orm(log)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return rapor_logu_to_entity(orm)


# ════════════════════════════════════════════
# RAPOR SCHEDULE
# ════════════════════════════════════════════

class SqlAlchemyRaporScheduleRepository(IRaporScheduleRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        is_aktif: bool = True,
    ) -> List[RaporSchedule]:
        query = self._db.query(RaporScheduleORM).options(
            joinedload(RaporScheduleORM.sablon),
        )
        if is_aktif:
            query = query.filter(RaporScheduleORM.is_aktif == True)
        orm_list = query.order_by(
            RaporScheduleORM.sablon_adi
        ).offset(skip).limit(limit).all()
        return [rapor_schedule_to_entity(o) for o in orm_list]

    def getir_id_ile(self, schedule_id: int) -> Optional[RaporSchedule]:
        orm = self._db.query(RaporScheduleORM).options(
            joinedload(RaporScheduleORM.sablon),
        ).filter(RaporScheduleORM.id == schedule_id).first()
        return rapor_schedule_to_entity(orm) if orm else None

    def olustur(self, schedule: RaporSchedule) -> RaporSchedule:
        orm = rapor_schedule_to_orm(schedule)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return rapor_schedule_to_entity(orm)

    def guncelle(self, schedule: RaporSchedule) -> RaporSchedule:
        orm = self._db.query(RaporScheduleORM).filter(RaporScheduleORM.id == schedule.id).first()
        if not orm:
            return None
        orm.sablon_id = schedule.sablon_id
        orm.sablon_adi = schedule.sablon_adi
        orm.periyod = schedule.periyod
        orm.saat = schedule.saat
        orm.alici_emailler = schedule.alici_emailler
        orm.format = schedule.format
        orm.is_aktif = schedule.is_aktif
        orm.son_calistirilma = schedule.son_calistirilma
        orm.guncelleme_tarihi = schedule.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return rapor_schedule_to_entity(orm)

    def sil(self, schedule_id: int) -> bool:
        orm = self._db.query(RaporScheduleORM).filter(RaporScheduleORM.id == schedule_id).first()
        if not orm:
            return False
        self._db.delete(orm)
        self._db.commit()
        return True
