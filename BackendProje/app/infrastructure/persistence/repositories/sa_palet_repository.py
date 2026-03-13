from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.core.entities.palet import Palet
from app.core.repositories.palet_repository import IPaletRepository
from app.infrastructure.persistence.mappers import palet_to_entity, palet_to_orm
from models import Palet as PaletORM, Lot as LotORM


class SqlAlchemyPaletRepository(IPaletRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        lot_id: Optional[int] = None,
        raf_id: Optional[int] = None,
        sadece_aktif: bool = True,
    ) -> List[Palet]:
        query = self._db.query(PaletORM).options(
            joinedload(PaletORM.lot),
            joinedload(PaletORM.raf),
        )
        if sadece_aktif:
            query = query.filter(PaletORM.aktif == True)
        if lot_id:
            query = query.filter(PaletORM.lot_id == lot_id)
        if raf_id:
            query = query.filter(PaletORM.raf_id == raf_id)
        orm_list = query.order_by(PaletORM.tarih.desc()).offset(skip).limit(limit).all()
        return [palet_to_entity(o) for o in orm_list]

    def getir_id_ile(self, palet_id: int) -> Optional[Palet]:
        orm = self._db.query(PaletORM).options(
            joinedload(PaletORM.lot).joinedload(LotORM.urun),
            joinedload(PaletORM.raf),
        ).filter(PaletORM.id == palet_id).first()
        return palet_to_entity(orm) if orm else None

    def getir_palet_no_ile(self, palet_no: str) -> Optional[Palet]:
        orm = self._db.query(PaletORM).options(
            joinedload(PaletORM.lot).joinedload(LotORM.urun),
            joinedload(PaletORM.raf),
        ).filter(PaletORM.palet_no == palet_no).first()
        return palet_to_entity(orm) if orm else None

    def olustur(self, palet: Palet) -> Palet:
        orm = palet_to_orm(palet)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return palet_to_entity(orm)

    def guncelle(self, palet: Palet) -> Palet:
        orm = self._db.query(PaletORM).filter(PaletORM.id == palet.id).first()
        if not orm:
            return None
        orm.lot_id = palet.lot_id
        orm.raf_id = palet.raf_id
        orm.palet_no = palet.palet_no
        orm.koli_adedi = palet.koli_adedi
        orm.palet_kg = palet.palet_kg
        orm.vardiya = palet.vardiya
        orm.aktif = palet.aktif
        self._db.commit()
        self._db.refresh(orm)
        return palet_to_entity(orm)

    def sil(self, palet_id: int) -> bool:
        orm = self._db.query(PaletORM).filter(PaletORM.id == palet_id).first()
        if not orm:
            return False
        orm.aktif = False
        self._db.commit()
        return True

    def sonraki_palet_no(self) -> str:
        son_palet = self._db.query(PaletORM).order_by(PaletORM.id.desc()).first()
        if son_palet and son_palet.palet_no.isdigit():
            return str(int(son_palet.palet_no) + 1)
        return "1000001"

    def getir_fifo_sirayla(self, urun_id: int) -> List[Palet]:
        """FIFO sıralamasıyla aktif paletleri döner.

        Sıralama: SKT asc (NULL en sona), üretim tarihi asc, palet tarihi asc.
        """
        orm_list = self._db.query(PaletORM).join(LotORM).filter(
            LotORM.urun_id == urun_id,
            LotORM.aktif == True,
            PaletORM.aktif == True,
            PaletORM.koli_adedi > 0,
        ).order_by(
            LotORM.son_kullanma_tarihi.asc().nulls_last(),
            LotORM.uretim_tarihi.asc().nulls_last(),
            PaletORM.tarih.asc(),
        ).all()
        return [palet_to_entity(o) for o in orm_list]
