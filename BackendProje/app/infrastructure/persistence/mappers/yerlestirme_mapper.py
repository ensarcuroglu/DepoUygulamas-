"""Yerleştirme Görevi domain mapper."""

from __future__ import annotations

from models import YerlestirmeGorevi as YerlestirmeGoreviORM
from app.core.entities.yerlestirme_gorevi import YerlestirmeGorevi


def yerlestirme_gorevi_to_entity(orm: YerlestirmeGoreviORM) -> YerlestirmeGorevi:
    return YerlestirmeGorevi(
        id=orm.id,
        palet_id=orm.palet_id,
        mal_kabul_irsaliye_id=orm.mal_kabul_irsaliye_id,
        tip=orm.tip,
        kaynak_raf_id=orm.kaynak_raf_id,
        onerilen_raf_id=orm.onerilen_raf_id,
        gerceklesen_raf_id=orm.gerceklesen_raf_id,
        durum=orm.durum,
        oncelik=orm.oncelik,
        atanan_kullanici_id=orm.atanan_kullanici_id,
        override_kullanici_id=orm.override_kullanici_id,
        override_neden=orm.override_neden,
        olusturma_tarihi=orm.olusturma_tarihi,
        baslama_tarihi=orm.baslama_tarihi,
        tamamlanma_tarihi=orm.tamamlanma_tarihi,
        iptal_nedeni=orm.iptal_nedeni,
    )


def yerlestirme_gorevi_to_orm(entity: YerlestirmeGorevi) -> YerlestirmeGoreviORM:
    return YerlestirmeGoreviORM(
        id=entity.id,
        palet_id=entity.palet_id,
        mal_kabul_irsaliye_id=entity.mal_kabul_irsaliye_id,
        tip=entity.tip,
        kaynak_raf_id=entity.kaynak_raf_id,
        onerilen_raf_id=entity.onerilen_raf_id,
        gerceklesen_raf_id=entity.gerceklesen_raf_id,
        durum=entity.durum,
        oncelik=entity.oncelik,
        atanan_kullanici_id=entity.atanan_kullanici_id,
        override_kullanici_id=entity.override_kullanici_id,
        override_neden=entity.override_neden,
        olusturma_tarihi=entity.olusturma_tarihi,
        baslama_tarihi=entity.baslama_tarihi,
        tamamlanma_tarihi=entity.tamamlanma_tarihi,
        iptal_nedeni=entity.iptal_nedeni,
    )
