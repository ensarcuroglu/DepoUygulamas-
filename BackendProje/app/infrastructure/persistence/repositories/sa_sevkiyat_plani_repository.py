from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session, joinedload

from app.core.entities.sevkiyat_plani import SevkiyatPlani
from app.core.repositories.sevkiyat_plani_repository import ISevkiyatPlaniRepository
from app.infrastructure.persistence.mappers import sevkiyat_plani_to_entity, sevkiyat_plani_to_orm
from models import SevkiyatPlani as SevkiyatPlaniORM


class SqlAlchemySevkiyatPlaniRepository(ISevkiyatPlaniRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        tarih_baslangic: Optional[date] = None,
        tarih_bitis: Optional[date] = None,
    ) -> List[SevkiyatPlani]:
        query = self._db.query(SevkiyatPlaniORM).options(
            joinedload(SevkiyatPlaniORM.siparis),
        )

        if durum:
            query = query.filter(SevkiyatPlaniORM.durum == durum)
        if tarih_baslangic:
            query = query.filter(SevkiyatPlaniORM.yukleme_tarihi >= tarih_baslangic)
        if tarih_bitis:
            query = query.filter(SevkiyatPlaniORM.yukleme_tarihi <= tarih_bitis)

        orm_list = query.order_by(
            SevkiyatPlaniORM.yukleme_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [sevkiyat_plani_to_entity(o) for o in orm_list]

    def getir_id_ile(self, plan_id: int) -> Optional[SevkiyatPlani]:
        orm = self._db.query(SevkiyatPlaniORM).options(
            joinedload(SevkiyatPlaniORM.siparis),
        ).filter(SevkiyatPlaniORM.id == plan_id).first()
        return sevkiyat_plani_to_entity(orm) if orm else None

    def getir_siparis_id_ile(self, siparis_id: int) -> Optional[SevkiyatPlani]:
        orm = self._db.query(SevkiyatPlaniORM).filter(
            SevkiyatPlaniORM.siparis_id == siparis_id
        ).first()
        return sevkiyat_plani_to_entity(orm) if orm else None

    def olustur(self, plan: SevkiyatPlani) -> SevkiyatPlani:
        orm = sevkiyat_plani_to_orm(plan)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return sevkiyat_plani_to_entity(orm)

    def guncelle(self, plan: SevkiyatPlani) -> SevkiyatPlani:
        orm = self._db.query(SevkiyatPlaniORM).filter(SevkiyatPlaniORM.id == plan.id).first()
        if not orm:
            return None
        orm.siparis_id = plan.siparis_id
        orm.tir_plaka = plan.tir_plaka
        orm.sofor_adi = plan.sofor_adi
        orm.sofor_telefon = plan.sofor_telefon
        orm.depo_kapi = plan.depo_kapi
        orm.yukleme_tarihi = plan.yukleme_tarihi
        orm.cikis_saati = plan.cikis_saati
        orm.varis_saati = plan.varis_saati
        orm.durum = plan.durum
        orm.notlar = plan.notlar
        orm.guncelleme_tarihi = plan.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return sevkiyat_plani_to_entity(orm)

    def sil(self, plan_id: int) -> bool:
        orm = self._db.query(SevkiyatPlaniORM).filter(SevkiyatPlaniORM.id == plan_id).first()
        if not orm:
            return False
        self._db.delete(orm)
        self._db.commit()
        return True
