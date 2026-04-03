from typing import Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.entities.stok_sayim import StokSayim, StokSayimKalemi
from app.core.repositories.stok_sayim_repository import IStokSayimRepository
from app.infrastructure.persistence.mappers import (
    stok_sayim_to_entity, stok_sayim_to_orm,
    stok_sayim_kalemi_to_entity, stok_sayim_kalemi_to_orm,
)
from models import (
    StokSayim as StokSayimORM,
    StokSayimKalemi as StokSayimKalemiORM,
    Urun as UrunORM,
    Lot as LotORM,
    Palet as PaletORM,
)


class SqlAlchemyStokSayimRepository(IStokSayimRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(self, skip: int = 0, limit: int = 100) -> List[StokSayim]:
        # selectinload: one-to-many ile offset/limit doğru çalışır (joinedload pagination bozar)
        orm_list = self._db.query(StokSayimORM).options(
            selectinload(StokSayimORM.sayim_kalemleri),
        ).order_by(
            StokSayimORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [stok_sayim_to_entity(o) for o in orm_list]

    def getir_id_ile(self, sayim_id: int) -> Optional[StokSayim]:
        orm = self._db.query(StokSayimORM).options(
            joinedload(StokSayimORM.sayim_kalemleri),
        ).filter(StokSayimORM.id == sayim_id).first()
        return stok_sayim_to_entity(orm) if orm else None

    def olustur(self, sayim: StokSayim) -> StokSayim:
        orm = stok_sayim_to_orm(sayim)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return stok_sayim_to_entity(orm)

    def guncelle(self, sayim: StokSayim) -> StokSayim:
        orm = self._db.query(StokSayimORM).filter(StokSayimORM.id == sayim.id).first()
        if not orm:
            return None
        orm.sayim_no = sayim.sayim_no
        orm.aciklama = sayim.aciklama
        orm.baslangic_tarihi = sayim.baslangic_tarihi
        orm.bitis_tarihi = sayim.bitis_tarihi
        orm.referans_stok_json = sayim.referans_stok_json
        orm.kontrol_eden_user_id = sayim.kontrol_eden_user_id
        orm.onaylayan_user_id = sayim.onaylayan_user_id
        orm.durum = sayim.durum
        orm.aktif = sayim.aktif
        self._db.commit()
        self._db.refresh(orm)
        return stok_sayim_to_entity(orm)

    def kalem_ekle(self, kalem: StokSayimKalemi) -> StokSayimKalemi:
        orm = stok_sayim_kalemi_to_orm(kalem)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return stok_sayim_kalemi_to_entity(orm)

    def kalem_guncelle(self, kalem: StokSayimKalemi) -> StokSayimKalemi:
        orm = self._db.query(StokSayimKalemiORM).filter(
            StokSayimKalemiORM.id == kalem.id
        ).first()
        if not orm:
            return None
        orm.sayim_id = kalem.sayim_id
        orm.urun_id = kalem.urun_id
        orm.sayilan_miktar = kalem.sayilan_miktar
        orm.notlar = kalem.notlar
        orm.user_id = kalem.user_id
        orm.sayim_tarihi = kalem.sayim_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return stok_sayim_kalemi_to_entity(orm)

    def kalem_getir_by_sayim_urun(self, sayim_id: int, urun_id: int) -> Optional[StokSayimKalemi]:
        orm = self._db.query(StokSayimKalemiORM).filter(
            StokSayimKalemiORM.sayim_id == sayim_id,
            StokSayimKalemiORM.urun_id == urun_id,
        ).first()
        return stok_sayim_kalemi_to_entity(orm) if orm else None

    def aktif_sayim_var_mi(self) -> bool:
        return self._db.query(StokSayimORM).filter(
            StokSayimORM.durum.in_(["devam_ediyor", "bitti"])
        ).first() is not None

    def stok_snapshot_getir(self) -> Dict[int, int]:
        rows = (
            self._db.query(
                UrunORM.id,
                func.coalesce(func.sum(PaletORM.koli_adedi), 0),
            )
            .outerjoin(LotORM, (LotORM.urun_id == UrunORM.id) & (LotORM.aktif == True))
            .outerjoin(PaletORM, (PaletORM.lot_id == LotORM.id) & (PaletORM.aktif == True))
            .filter(UrunORM.aktif == True)
            .group_by(UrunORM.id)
            .all()
        )
        return {urun_id: int(toplam) for urun_id, toplam in rows}
