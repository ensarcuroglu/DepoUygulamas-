"""SQLAlchemy BelgeTaslagi repository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.entities.belge_taslagi import BelgeTaslagi
from app.core.exceptions import KayitBulunamadiError
from app.core.repositories.belge_taslagi_repository import IBelgeTaslagiRepository
from app.infrastructure.persistence.mappers.belge_taslagi_mapper import (
    belge_taslagi_to_entity,
    belge_taslagi_to_orm,
)
from models import BelgeTaslagi as BelgeTaslagiORM


class SqlAlchemyBelgeTaslagiRepository(IBelgeTaslagiRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        depo_id: Optional[int] = None,
        max_confidence: Optional[float] = None,
    ) -> list[BelgeTaslagi]:
        query = self._db.query(BelgeTaslagiORM)
        if durum:
            query = query.filter(BelgeTaslagiORM.durum == durum)
        if depo_id:
            query = query.filter(BelgeTaslagiORM.depo_id == depo_id)
        if max_confidence is not None:
            query = query.filter(BelgeTaslagiORM.confidence_skoru < max_confidence)
        orm_list = (
            query.order_by(BelgeTaslagiORM.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [belge_taslagi_to_entity(orm) for orm in orm_list]

    def getir_id_ile(self, taslak_id: int) -> Optional[BelgeTaslagi]:
        orm = self._db.query(BelgeTaslagiORM).filter(BelgeTaslagiORM.id == taslak_id).first()
        return belge_taslagi_to_entity(orm) if orm else None

    def olustur(self, taslak: BelgeTaslagi, auto_commit: bool = False) -> BelgeTaslagi:
        orm = belge_taslagi_to_orm(taslak)
        orm.id = None
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return belge_taslagi_to_entity(orm)

    def guncelle(self, taslak: BelgeTaslagi, auto_commit: bool = False) -> BelgeTaslagi:
        orm = self._db.query(BelgeTaslagiORM).filter(BelgeTaslagiORM.id == taslak.id).first()
        if not orm:
            raise KayitBulunamadiError("Belge Taslagi", taslak.id)

        orm.kaynak_dosya_yolu = taslak.kaynak_dosya_yolu
        orm.belge_tipi = taslak.belge_tipi
        orm.ham_json = taslak.ham_json
        orm.durum = taslak.durum
        orm.confidence_skoru = taslak.confidence_skoru
        orm.olusturan_kullanici_id = taslak.olusturan_kullanici_id
        orm.depo_id = taslak.depo_id
        orm.mal_kabul_irsaliye_id = taslak.mal_kabul_irsaliye_id
        orm.updated_at = taslak.updated_at

        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return belge_taslagi_to_entity(orm)
