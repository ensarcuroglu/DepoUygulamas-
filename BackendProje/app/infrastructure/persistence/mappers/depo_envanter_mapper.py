"""Depo & envanter domain mapper'ları — Depo, Raf, Lot, Palet."""

from __future__ import annotations

from models import (
    Depo as DepoORM,
    Raf as RafORM,
    Lot as LotORM,
    Palet as PaletORM,
)
from app.core.entities.depo import Depo
from app.core.entities.raf import Raf
from app.core.entities.lot import Lot
from app.core.entities.palet import Palet, LotBilgi, UrunBilgi, RafBilgi


def depo_to_entity(orm: DepoORM) -> Depo:
    return Depo(
        id=orm.id,
        isim=orm.isim,
        adres=orm.adres or "",
        aciklama=orm.aciklama or "",
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def depo_to_orm(entity: Depo) -> DepoORM:
    return DepoORM(
        id=entity.id,
        isim=entity.isim,
        adres=entity.adres,
        aciklama=entity.aciklama,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def raf_to_entity(orm: RafORM) -> Raf:
    return Raf(
        id=orm.id,
        depo_id=orm.depo_id,
        kod=orm.kod,
        bolge=orm.bolge or "",
        kapasite=orm.kapasite,
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def raf_to_orm(entity: Raf) -> RafORM:
    return RafORM(
        id=entity.id,
        depo_id=entity.depo_id,
        kod=entity.kod,
        bolge=entity.bolge,
        kapasite=entity.kapasite,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def lot_to_entity(orm: LotORM) -> Lot:
    return Lot(
        id=orm.id,
        urun_id=orm.urun_id,
        lot_no=orm.lot_no,
        parti_no=orm.parti_no,
        uretim_tarihi=orm.uretim_tarihi,
        son_kullanma_tarihi=orm.son_kullanma_tarihi,
        aciklama=orm.aciklama or "",
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def lot_to_orm(entity: Lot) -> LotORM:
    return LotORM(
        id=entity.id,
        urun_id=entity.urun_id,
        lot_no=entity.lot_no,
        parti_no=entity.parti_no,
        uretim_tarihi=entity.uretim_tarihi,
        son_kullanma_tarihi=entity.son_kullanma_tarihi,
        aciklama=entity.aciklama,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def _build_urun_bilgi(orm_lot) -> UrunBilgi | None:
    """ORM Lot'un eager-loaded urun ilişkisinden UrunBilgi oluşturur."""
    urun = getattr(orm_lot, "urun", None)
    if urun is None:
        return None
    return UrunBilgi(
        id=urun.id,
        isim=urun.isim,
        ean=urun.ean,
        barkod=urun.barkod,
    )


def _build_lot_bilgi(orm) -> LotBilgi | None:
    """ORM Palet'in eager-loaded lot ilişkisinden LotBilgi oluşturur."""
    lot = getattr(orm, "lot", None)
    if lot is None:
        return None
    return LotBilgi(
        id=lot.id,
        lot_no=lot.lot_no,
        urun_id=lot.urun_id,
        uretim_tarihi=lot.uretim_tarihi,
        son_kullanma_tarihi=lot.son_kullanma_tarihi,
        urun=_build_urun_bilgi(lot),
    )


def _build_raf_bilgi(orm) -> RafBilgi | None:
    """ORM Palet'in eager-loaded raf ilişkisinden RafBilgi oluşturur."""
    raf = getattr(orm, "raf", None)
    if raf is None:
        return None
    return RafBilgi(
        id=raf.id,
        kod=raf.kod,
        bolge=raf.bolge or "",
    )


def palet_to_entity(orm: PaletORM) -> Palet:
    return Palet(
        id=orm.id,
        lot_id=orm.lot_id,
        raf_id=orm.raf_id,
        palet_no=orm.palet_no,
        koli_adedi=orm.koli_adedi,
        palet_kg=orm.palet_kg,
        vardiya=orm.vardiya,
        tarih=orm.tarih,
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
        lot=_build_lot_bilgi(orm),
        raf=_build_raf_bilgi(orm),
    )


def palet_to_orm(entity: Palet) -> PaletORM:
    return PaletORM(
        id=entity.id,
        lot_id=entity.lot_id,
        raf_id=entity.raf_id,
        palet_no=entity.palet_no,
        koli_adedi=entity.koli_adedi,
        palet_kg=entity.palet_kg,
        vardiya=entity.vardiya,
        tarih=entity.tarih,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )

