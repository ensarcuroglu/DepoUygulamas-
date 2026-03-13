from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.core.entities.destek_talebi import DestekTalebi
from app.core.repositories.destek_talebi_repository import IDestekTalebiRepository
from app.infrastructure.persistence.mappers import destek_talebi_to_entity, destek_talebi_to_orm
from models import DestekTalebi as DestekTalebiORM


class SqlAlchemyDestekTalebiRepository(IDestekTalebiRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        kullanici_id: Optional[int] = None,
        durum: Optional[str] = None,
    ) -> List[DestekTalebi]:
        query = self._db.query(DestekTalebiORM).options(
            joinedload(DestekTalebiORM.kullanici),
        )
        if kullanici_id:
            query = query.filter(DestekTalebiORM.kullanici_id == kullanici_id)
        if durum:
            query = query.filter(DestekTalebiORM.durum == durum)
        orm_list = query.order_by(
            DestekTalebiORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [destek_talebi_to_entity(o) for o in orm_list]

    def getir_id_ile(self, talep_id: int) -> Optional[DestekTalebi]:
        orm = self._db.query(DestekTalebiORM).options(
            joinedload(DestekTalebiORM.kullanici),
        ).filter(DestekTalebiORM.id == talep_id).first()
        return destek_talebi_to_entity(orm) if orm else None

    def olustur(self, talep: DestekTalebi) -> DestekTalebi:
        orm = destek_talebi_to_orm(talep)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return destek_talebi_to_entity(orm)

    def guncelle(self, talep: DestekTalebi) -> DestekTalebi:
        orm = self._db.query(DestekTalebiORM).filter(DestekTalebiORM.id == talep.id).first()
        if not orm:
            return None
        orm.konu = talep.konu
        orm.kategori = talep.kategori
        orm.oncelik = talep.oncelik
        orm.durum = talep.durum
        orm.aciklama = talep.aciklama
        orm.admin_cevabi = talep.admin_cevabi
        orm.guncelleme_tarihi = talep.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return destek_talebi_to_entity(orm)
