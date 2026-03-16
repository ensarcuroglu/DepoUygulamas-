from typing import List, Optional
from sqlalchemy.orm import Session

from app.core.entities.sistem_log import SistemLog
from app.core.repositories.sistem_log_repository import ISistemLogRepository
from app.infrastructure.persistence.mappers import sistem_log_to_entity, sistem_log_to_orm
from models import SistemLog as SistemLogORM


class SqlAlchemySistemLogRepository(ISistemLogRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        modul: Optional[str] = None,
        islem_tipi: Optional[str] = None,
    ) -> List[SistemLog]:
        query = self._db.query(SistemLogORM)
        if modul:
            query = query.filter(SistemLogORM.modul == modul)
        if islem_tipi:
            query = query.filter(SistemLogORM.islem_tipi == islem_tipi)
        orm_list = query.order_by(SistemLogORM.tarih.desc()).offset(skip).limit(limit).all()
        return [sistem_log_to_entity(o) for o in orm_list]

    def olustur(self, log: SistemLog, auto_commit: bool = True) -> SistemLog:
        orm = sistem_log_to_orm(log)
        orm.id = None
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
        else:
            self._db.flush()
        self._db.refresh(orm)
        return sistem_log_to_entity(orm)
