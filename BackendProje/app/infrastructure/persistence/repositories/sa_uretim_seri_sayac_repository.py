from datetime import date

from sqlalchemy.orm import Session

from app.core.repositories.uretim_seri_sayac_repository import IUretimSeriSayacRepository
from models import UretimSeriSayac as UretimSeriSayacORM


class SqlAlchemyUretimSeriSayacRepository(IUretimSeriSayacRepository):

    def __init__(self, db: Session):
        self._db = db

    def artir_ve_dondur(self, tarih: date) -> int:
        """SELECT ... FOR UPDATE ile atomik artış. Transaction rollback'te gap kabul edilir."""
        kayit = (
            self._db.query(UretimSeriSayacORM)
            .filter(UretimSeriSayacORM.tarih == tarih)
            .with_for_update()
            .first()
        )
        if kayit is None:
            kayit = UretimSeriSayacORM(tarih=tarih, son_seri_no=1)
            self._db.add(kayit)
            self._db.flush()
            return 1

        kayit.son_seri_no += 1
        self._db.flush()
        return kayit.son_seri_no
