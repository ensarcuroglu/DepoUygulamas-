from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.repositories.uretim_seri_sayac_repository import IUretimSeriSayacRepository
from models import UretimSeriSayac as UretimSeriSayacORM


class SqlAlchemyUretimSeriSayacRepository(IUretimSeriSayacRepository):

    def __init__(self, db: Session):
        self._db = db

    def artir_ve_dondur(self, tarih: date, prefix: str = "PRD") -> int:
        kayit = (
            self._db.query(UretimSeriSayacORM)
            .filter(
                UretimSeriSayacORM.prefix == prefix,
                UretimSeriSayacORM.tarih == tarih,
            )
            .first()
        )

        if not kayit:
            yeni_kayit = UretimSeriSayacORM(prefix=prefix, tarih=tarih, son_seri_no=1)
            try:
                with self._db.begin_nested():
                    self._db.add(yeni_kayit)
                    self._db.flush()
                    return 1
            except IntegrityError:
                # TEK DEĞİŞİKLİK BURADA: Sadece obje session'da takılı kaldıysa expunge et.
                if yeni_kayit in self._db:
                    self._db.expunge(yeni_kayit)

        kilitli_kayit = (
            self._db.query(UretimSeriSayacORM)
            .filter(
                UretimSeriSayacORM.prefix == prefix,
                UretimSeriSayacORM.tarih == tarih,
            )
            .with_for_update()
            .populate_existing()
            .first()
        )
        
        kilitli_kayit.son_seri_no += 1
        self._db.flush()
        return kilitli_kayit.son_seri_no