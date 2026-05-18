"""SQLAlchemy AsistanAksiyonTaslagi repository."""

from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from app.core.entities.asistan_aksiyon_taslagi import AsistanAksiyonTaslagi
from app.core.repositories.asistan_aksiyon_taslagi_repository import (
    IAsistanAksiyonTaslagiRepository,
)
from app.infrastructure.persistence.mappers.asistan_aksiyon_taslagi_mapper import (
    asistan_aksiyon_taslagi_to_entity,
    asistan_aksiyon_taslagi_to_orm,
)
from core.api_exceptions import NotFoundError
from models import AsistanAksiyonTaslagi as AsistanAksiyonTaslagiORM


class SqlAlchemyAsistanAksiyonTaslagiRepository(IAsistanAksiyonTaslagiRepository):
    def __init__(self, db: Session) -> None:
        self._db = db

    def getir_id_ile(
        self, taslak_id: int, kilitli_mi: bool = False
    ) -> Optional[AsistanAksiyonTaslagi]:
        query = self._db.query(AsistanAksiyonTaslagiORM).filter(
            AsistanAksiyonTaslagiORM.id == taslak_id
        )
        if kilitli_mi:
            query = query.with_for_update()
        orm = query.first()
        return asistan_aksiyon_taslagi_to_entity(orm) if orm else None

    def getir_idempotency_ile(
        self, idempotency_key: str
    ) -> Optional[AsistanAksiyonTaslagi]:
        orm = (
            self._db.query(AsistanAksiyonTaslagiORM)
            .filter(AsistanAksiyonTaslagiORM.idempotency_key == idempotency_key)
            .first()
        )
        return asistan_aksiyon_taslagi_to_entity(orm) if orm else None

    def getir_hepsi(
        self,
        kullanici_id: Optional[int] = None,
        durum: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsistanAksiyonTaslagi]:
        query = self._db.query(AsistanAksiyonTaslagiORM)
        if kullanici_id is not None:
            query = query.filter(AsistanAksiyonTaslagiORM.kullanici_id == kullanici_id)
        if durum:
            query = query.filter(AsistanAksiyonTaslagiORM.durum == durum)
        orm_list = (
            query.order_by(AsistanAksiyonTaslagiORM.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [asistan_aksiyon_taslagi_to_entity(orm) for orm in orm_list]

    def olustur(
        self,
        taslak: AsistanAksiyonTaslagi,
        auto_commit: bool = False,
    ) -> AsistanAksiyonTaslagi:
        orm = asistan_aksiyon_taslagi_to_orm(taslak)
        orm.id = None
        self._db.add(orm)
        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return asistan_aksiyon_taslagi_to_entity(orm)

    def guncelle(
        self,
        taslak: AsistanAksiyonTaslagi,
        auto_commit: bool = False,
    ) -> AsistanAksiyonTaslagi:
        orm = (
            self._db.query(AsistanAksiyonTaslagiORM)
            .filter(AsistanAksiyonTaslagiORM.id == taslak.id)
            .first()
        )
        if not orm:
            raise NotFoundError("Asistan Aksiyon Taslagi", taslak.id)

        orm.durum = taslak.durum
        orm.ozet = taslak.ozet
        orm.sonuc_json = taslak.sonuc_json
        orm.hata_mesaji = taslak.hata_mesaji
        orm.executed_at = taslak.executed_at

        if auto_commit:
            self._db.commit()
            self._db.refresh(orm)
        else:
            self._db.flush()
        return asistan_aksiyon_taslagi_to_entity(orm)
