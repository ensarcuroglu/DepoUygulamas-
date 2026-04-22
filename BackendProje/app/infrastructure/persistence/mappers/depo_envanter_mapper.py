"""Depo & envanter domain mapper'ları — Depo, Raf, Lot, Palet."""

from __future__ import annotations

from models import (
    Depo as DepoORM,
    Zon as ZonORM,
    Raf as RafORM,
    Lot as LotORM,
    Palet as PaletORM,
)
from app.core.entities.depo import Depo
from app.core.entities.zon import Zon
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


def zon_to_entity(orm: ZonORM) -> Zon:
    return Zon(
        id=orm.id,
        depo_id=orm.depo_id,
        isim=orm.isim,
        tip=orm.tip,
        kod=orm.kod,
        aciklama=orm.aciklama or "",
        sira=orm.sira,
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def zon_to_orm(entity: Zon) -> ZonORM:
    return ZonORM(
        id=entity.id,
        depo_id=entity.depo_id,
        isim=entity.isim,
        tip=entity.tip,
        kod=entity.kod,
        aciklama=entity.aciklama,
        sira=entity.sira,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def raf_to_entity(orm: RafORM) -> Raf:
    return Raf(
        id=orm.id,
        depo_id=orm.depo_id,
        zon_id=orm.zon_id,
        kod=orm.kod,
        bolge=orm.bolge or "",
        kapasite=orm.kapasite,
        max_agirlik_kg=orm.max_agirlik_kg,
        koridor=orm.koridor or "",
        kat=orm.kat or 0,
        goz=orm.goz or 0,
        aktif=orm.aktif,
        is_staging=bool(orm.is_staging),
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def raf_to_orm(entity: Raf) -> RafORM:
    return RafORM(
        id=entity.id,
        depo_id=entity.depo_id,
        zon_id=entity.zon_id,
        kod=entity.kod,
        bolge=entity.bolge,
        kapasite=entity.kapasite,
        max_agirlik_kg=entity.max_agirlik_kg,
        koridor=entity.koridor,
        kat=entity.kat,
        goz=entity.goz,
        aktif=entity.aktif,
        is_staging=entity.is_staging,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def lot_to_entity(orm: LotORM) -> Lot:
    urun = getattr(orm, "urun", None)
    marka = getattr(urun, "marka", None) if urun is not None else None
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
        urun_isim=getattr(urun, "isim", None),
        marka_id=getattr(marka, "id", None),
        marka_isim=getattr(marka, "isim", None),
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
        kaynak=orm.kaynak,
        durum=orm.durum,
        uretim_tarihi=orm.uretim_tarihi,
        lot_no=orm.lot_no,
        kabul_eden_kullanici_id=orm.kabul_eden_kullanici_id,
        kabul_tarihi=orm.kabul_tarihi,
        iptal_sebebi=orm.iptal_sebebi,
        uretim_hatti=getattr(orm, "uretim_hatti", None),
        makine_kodu=getattr(orm, "makine_kodu", None),
        operator_kullanici_id=getattr(orm, "operator_kullanici_id", None),
        brut_kg=getattr(orm, "brut_kg", None),
        net_kg=getattr(orm, "net_kg", None),
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
        kaynak=entity.kaynak,
        durum=entity.durum,
        uretim_tarihi=entity.uretim_tarihi,
        lot_no=entity.lot_no,
        kabul_eden_kullanici_id=entity.kabul_eden_kullanici_id,
        kabul_tarihi=entity.kabul_tarihi,
        iptal_sebebi=entity.iptal_sebebi,
        uretim_hatti=entity.uretim_hatti,
        makine_kodu=entity.makine_kodu,
        operator_kullanici_id=entity.operator_kullanici_id,
        brut_kg=entity.brut_kg,
        net_kg=entity.net_kg,
    )
