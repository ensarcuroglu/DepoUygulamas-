"""Rapor domain mapper'ları — RaporSablonu, RaporLogu, RaporSchedule."""

from __future__ import annotations

from models import (
    RaporSablonu as RaporSablonuORM,
    RaporLogu as RaporLoguORM,
    RaporSchedule as RaporScheduleORM,
)
from app.core.entities.rapor import RaporSablonu, RaporLogu, RaporSchedule


def rapor_sablonu_to_entity(orm: RaporSablonuORM) -> RaporSablonu:
    return RaporSablonu(
        id=orm.id,
        ad=orm.ad,
        tur=orm.tur,
        aciklama=orm.aciklama or "",
        config=orm.config,
        olusturan_kullanici_id=orm.olusturan_kullanici_id,
        is_aktif=orm.is_aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
    )


def rapor_sablonu_to_orm(entity: RaporSablonu) -> RaporSablonuORM:
    return RaporSablonuORM(
        id=entity.id,
        ad=entity.ad,
        tur=entity.tur,
        aciklama=entity.aciklama,
        config=entity.config,
        olusturan_kullanici_id=entity.olusturan_kullanici_id,
        is_aktif=entity.is_aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
    )


def rapor_logu_to_entity(orm: RaporLoguORM) -> RaporLogu:
    return RaporLogu(
        id=orm.id,
        sablon_id=orm.sablon_id,
        kullanici_id=orm.kullanici_id,
        parametreler=orm.parametreler,
        durum=orm.durum,
        hata_mesaji=orm.hata_mesaji,
        olusturma_tarihi=orm.olusturma_tarihi,
        tamamlanma_tarihi=orm.tamamlanma_tarihi,
    )


def rapor_logu_to_orm(entity: RaporLogu) -> RaporLoguORM:
    return RaporLoguORM(
        id=entity.id,
        sablon_id=entity.sablon_id,
        kullanici_id=entity.kullanici_id,
        parametreler=entity.parametreler,
        durum=entity.durum,
        hata_mesaji=entity.hata_mesaji,
        olusturma_tarihi=entity.olusturma_tarihi,
        tamamlanma_tarihi=entity.tamamlanma_tarihi,
    )


def rapor_schedule_to_entity(orm: RaporScheduleORM) -> RaporSchedule:
    return RaporSchedule(
        id=orm.id,
        sablon_id=orm.sablon_id,
        sablon_adi=orm.sablon_adi,
        periyod=orm.periyod,
        saat=orm.saat,
        alici_emailler=orm.alici_emailler,
        format=orm.format,
        is_aktif=orm.is_aktif,
        son_calistirilma=orm.son_calistirilma,
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
    )


def rapor_schedule_to_orm(entity: RaporSchedule) -> RaporScheduleORM:
    return RaporScheduleORM(
        id=entity.id,
        sablon_id=entity.sablon_id,
        sablon_adi=entity.sablon_adi,
        periyod=entity.periyod,
        saat=entity.saat,
        alici_emailler=entity.alici_emailler,
        format=entity.format,
        is_aktif=entity.is_aktif,
        son_calistirilma=entity.son_calistirilma,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
    )
