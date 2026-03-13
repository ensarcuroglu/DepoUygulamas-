from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.core.entities.stok_sayim import StokSayim, StokSayimKalemi
from app.core.repositories.stok_sayim_repository import IStokSayimRepository
from app.infrastructure.persistence.mappers import (
    stok_sayim_to_entity, stok_sayim_to_orm,
    stok_sayim_kalemi_to_entity, stok_sayim_kalemi_to_orm,
)
from models import StokSayim as StokSayimORM, StokSayimKalemi as StokSayimKalemiORM


class SqlAlchemyStokSayimRepository(IStokSayimRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(self, skip: int = 0, limit: int = 100) -> List[StokSayim]:
        orm_list = self._db.query(StokSayimORM).options(
            joinedload(StokSayimORM.sayim_kalemleri),
            joinedload(StokSayimORM.kontrol_eden),
        ).order_by(
            StokSayimORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [stok_sayim_to_entity(o) for o in orm_list]

    def getir_id_ile(self, sayim_id: int) -> Optional[StokSayim]:
        orm = self._db.query(StokSayimORM).options(
            joinedload(StokSayimORM.sayim_kalemleri),
            joinedload(StokSayimORM.kontrol_eden),
            joinedload(StokSayimORM.onaylayan),
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
