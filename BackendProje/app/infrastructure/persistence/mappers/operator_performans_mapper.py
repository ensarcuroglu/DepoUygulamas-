"""Operatör Performans (LMS) ORM ↔ entity mapper'ları."""

from __future__ import annotations

from models import (
    GorevPerformansEvent as GorevPerformansEventORM,
    OperatorVardiyaMetrikleri as OperatorVardiyaMetrikleriORM,
)
from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    OperatorVardiyaMetrikleri,
)


def gorev_performans_event_to_entity(orm: GorevPerformansEventORM) -> GorevPerformansEvent:
    return GorevPerformansEvent(
        id=orm.id,
        event_uuid=orm.event_uuid,
        event_tipi=orm.event_tipi,
        gorev_tipi=orm.gorev_tipi,
        gorev_id=orm.gorev_id,
        kullanici_id=orm.kullanici_id,
        depo_id=orm.depo_id,
        sure_saniye=orm.sure_saniye,
        iptal_nedeni=orm.iptal_nedeni,
        payload=orm.payload,
        aggregate_edildi=orm.aggregate_edildi,
        rabbitmq_yayinlandi=orm.rabbitmq_yayinlandi,
        rabbitmq_yayin_tarihi=orm.rabbitmq_yayin_tarihi,
        rabbitmq_deneme_sayisi=orm.rabbitmq_deneme_sayisi,
        rabbitmq_son_hata=orm.rabbitmq_son_hata,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def gorev_performans_event_to_orm(entity: GorevPerformansEvent) -> GorevPerformansEventORM:
    return GorevPerformansEventORM(
        event_uuid=entity.event_uuid,
        event_tipi=entity.event_tipi,
        gorev_tipi=entity.gorev_tipi,
        gorev_id=entity.gorev_id,
        kullanici_id=entity.kullanici_id,
        depo_id=entity.depo_id,
        sure_saniye=entity.sure_saniye,
        iptal_nedeni=entity.iptal_nedeni,
        payload=entity.payload,
        aggregate_edildi=entity.aggregate_edildi,
        rabbitmq_yayinlandi=entity.rabbitmq_yayinlandi,
        rabbitmq_yayin_tarihi=entity.rabbitmq_yayin_tarihi,
        rabbitmq_deneme_sayisi=entity.rabbitmq_deneme_sayisi,
        rabbitmq_son_hata=entity.rabbitmq_son_hata,
    )


def operator_vardiya_to_entity(orm: OperatorVardiyaMetrikleriORM) -> OperatorVardiyaMetrikleri:
    return OperatorVardiyaMetrikleri(
        id=orm.id,
        kullanici_id=orm.kullanici_id,
        depo_id=orm.depo_id,
        vardiya_tarihi=orm.vardiya_tarihi,
        tamamlanan_yerlestirme=orm.tamamlanan_yerlestirme,
        tamamlanan_toplama=orm.tamamlanan_toplama,
        iptal_sayisi=orm.iptal_sayisi,
        toplam_aktif_saniye=orm.toplam_aktif_saniye,
        ortalama_gorev_suresi_sn=orm.ortalama_gorev_suresi_sn,
        son_guncelleme=orm.son_guncelleme,
    )
