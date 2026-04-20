from sqlalchemy.orm import Session

from app.core.entities.palet_durum_log import PaletDurumLog
from app.core.repositories.palet_durum_log_repository import IPaletDurumLogRepository
from models import PaletDurumLog as PaletDurumLogORM


class SqlAlchemyPaletDurumLogRepository(IPaletDurumLogRepository):

    def __init__(self, db: Session):
        self._db = db

    def olustur(self, log: PaletDurumLog, auto_commit: bool = False) -> PaletDurumLog:
        orm = PaletDurumLogORM(
            palet_id=log.palet_id,
            eski_durum=log.eski_durum,
            yeni_durum=log.yeni_durum,
            degistiren_kullanici_id=log.degistiren_kullanici_id,
            sebep=log.sebep,
            degisim_tarihi=log.degisim_tarihi,
        )
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        log.id = orm.id
        return log
