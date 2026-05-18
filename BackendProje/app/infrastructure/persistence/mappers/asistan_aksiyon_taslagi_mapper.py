"""AsistanAksiyonTaslagi ORM <-> domain mapper."""

from __future__ import annotations

from app.core.entities.asistan_aksiyon_taslagi import AsistanAksiyonTaslagi
from models import AsistanAksiyonTaslagi as AsistanAksiyonTaslagiORM


def asistan_aksiyon_taslagi_to_entity(
    orm: AsistanAksiyonTaslagiORM,
) -> AsistanAksiyonTaslagi:
    return AsistanAksiyonTaslagi(
        id=orm.id,
        kullanici_id=orm.kullanici_id,
        rol=orm.rol,
        tool_id=orm.tool_id,
        payload_json=orm.payload_json or {},
        durum=orm.durum,
        ozet=orm.ozet,
        idempotency_key=orm.idempotency_key,
        sonuc_json=orm.sonuc_json,
        hata_mesaji=orm.hata_mesaji,
        created_at=orm.created_at,
        expires_at=orm.expires_at,
        executed_at=orm.executed_at,
    )


def asistan_aksiyon_taslagi_to_orm(
    entity: AsistanAksiyonTaslagi,
) -> AsistanAksiyonTaslagiORM:
    return AsistanAksiyonTaslagiORM(
        id=entity.id,
        kullanici_id=entity.kullanici_id,
        rol=entity.rol,
        tool_id=entity.tool_id,
        payload_json=entity.payload_json,
        durum=entity.durum,
        ozet=entity.ozet,
        idempotency_key=entity.idempotency_key,
        sonuc_json=entity.sonuc_json,
        hata_mesaji=entity.hata_mesaji,
        created_at=entity.created_at,
        expires_at=entity.expires_at,
        executed_at=entity.executed_at,
    )
