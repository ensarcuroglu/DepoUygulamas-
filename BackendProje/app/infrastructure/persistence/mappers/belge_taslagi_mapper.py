"""BelgeTaslagi ORM <-> domain mapper."""

from __future__ import annotations

from app.core.entities.belge_taslagi import BelgeTaslagi
from models import BelgeTaslagi as BelgeTaslagiORM


def belge_taslagi_to_entity(orm: BelgeTaslagiORM) -> BelgeTaslagi:
    return BelgeTaslagi(
        id=orm.id,
        kaynak_dosya_yolu=orm.kaynak_dosya_yolu,
        belge_tipi=orm.belge_tipi,
        ham_json=orm.ham_json or {},
        durum=orm.durum,
        confidence_skoru=float(orm.confidence_skoru or 0.0),
        olusturan_kullanici_id=orm.olusturan_kullanici_id,
        depo_id=orm.depo_id,
        mal_kabul_irsaliye_id=orm.mal_kabul_irsaliye_id,
        created_at=orm.created_at,
        updated_at=orm.updated_at,
    )


def belge_taslagi_to_orm(entity: BelgeTaslagi) -> BelgeTaslagiORM:
    return BelgeTaslagiORM(
        id=entity.id,
        kaynak_dosya_yolu=entity.kaynak_dosya_yolu,
        belge_tipi=entity.belge_tipi,
        ham_json=entity.ham_json,
        durum=entity.durum,
        confidence_skoru=entity.confidence_skoru,
        olusturan_kullanici_id=entity.olusturan_kullanici_id,
        depo_id=entity.depo_id,
        mal_kabul_irsaliye_id=entity.mal_kabul_irsaliye_id,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )
