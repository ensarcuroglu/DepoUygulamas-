from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.core.entities.urun import Urun
from app.core.repositories.urun_repository import IUrunRepository
from app.infrastructure.persistence.mappers import urun_to_entity, urun_to_orm
from models import Urun as UrunORM


class SqlAlchemyUrunRepository(IUrunRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        search: Optional[str] = None,
        kategori_id: Optional[int] = None,
        marka_id: Optional[int] = None,
        sadece_aktif: bool = True,
    ) -> List[Urun]:
        query = self._db.query(UrunORM).options(
            joinedload(UrunORM.marka),
            joinedload(UrunORM.kategori),
        )

        if sadece_aktif:
            query = query.filter(UrunORM.aktif == True)

        if search:
            query = query.filter(
                or_(
                    UrunORM.isim.ilike(f"%{search}%"),
                    UrunORM.barkod.ilike(f"%{search}%"),
                    UrunORM.ean.ilike(f"%{search}%"),
                    UrunORM.aciklama.ilike(f"%{search}%"),
                )
            )

        if kategori_id:
            query = query.filter(UrunORM.kategori_id == kategori_id)

        if marka_id:
            query = query.filter(UrunORM.marka_id == marka_id)

        return [urun_to_entity(o) for o in query.offset(skip).limit(limit).all()]

    def getir_id_ile(self, urun_id: int) -> Optional[Urun]:
        orm = self._db.query(UrunORM).options(
            joinedload(UrunORM.marka),
            joinedload(UrunORM.kategori),
            joinedload(UrunORM.tedarikci),
        ).filter(UrunORM.id == urun_id).first()
        return urun_to_entity(orm) if orm else None

    def getir_barkod_ile(self, barkod: str) -> Optional[Urun]:
        orm = self._db.query(UrunORM).options(
            joinedload(UrunORM.marka),
            joinedload(UrunORM.kategori),
        ).filter(
            or_(UrunORM.barkod == barkod, UrunORM.ean == barkod)
        ).first()
        return urun_to_entity(orm) if orm else None

    def getir_ean_ile(self, ean: str) -> Optional[Urun]:
        orm = self._db.query(UrunORM).options(
            joinedload(UrunORM.marka),
            joinedload(UrunORM.kategori),
        ).filter(UrunORM.ean == ean, UrunORM.aktif == True).first()
        return urun_to_entity(orm) if orm else None

    def olustur(self, urun: Urun) -> Urun:
        orm = urun_to_orm(urun)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return urun_to_entity(orm)

    def guncelle(self, urun: Urun) -> Urun:
        orm = self._db.query(UrunORM).filter(UrunORM.id == urun.id).first()
        if not orm:
            return None
        orm.isim = urun.isim
        orm.marka_id = urun.marka_id
        orm.kategori_id = urun.kategori_id
        orm.tedarikci_id = urun.tedarikci_id
        orm.ean = urun.ean
        orm.barkod = urun.barkod
        orm.ic_adet = urun.ic_adet
        orm.gramaj = urun.gramaj
        orm.birim = urun.birim
        orm.fiyat = urun.fiyat
        orm.min_stok = urun.min_stok
        orm.aciklama = urun.aciklama
        orm.aktif = urun.aktif
        orm.guncelleme_tarihi = urun.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return urun_to_entity(orm)

    def sil(self, urun_id: int) -> bool:
        orm = self._db.query(UrunORM).filter(UrunORM.id == urun_id).first()
        if not orm:
            return False
        orm.aktif = False
        from datetime import datetime
        orm.guncelleme_tarihi = datetime.utcnow()
        self._db.commit()
        return True

    def getir_kritik_stoklar(self) -> List[Urun]:
        orm_list = self._db.query(UrunORM).options(
            joinedload(UrunORM.marka),
            joinedload(UrunORM.kategori),
        ).filter(
            UrunORM.aktif == True,
            UrunORM.stok_miktari <= UrunORM.min_stok,
        ).all()
        return [urun_to_entity(o) for o in orm_list]
