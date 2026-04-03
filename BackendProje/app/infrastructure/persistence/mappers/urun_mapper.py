"""Ürün domain mapper'ları — Urun, StokHareketi."""

from __future__ import annotations

from models import (
    Urun as UrunORM,
    StokHareketi as StokHareketiORM,
)
from app.core.entities.urun import Urun
from app.core.entities.stok_hareketi import StokHareketi


def urun_to_entity(orm: UrunORM) -> Urun:
    return Urun(
        id=orm.id,
        isim=orm.isim,
        marka_id=orm.marka_id,
        kategori_id=orm.kategori_id,
        tedarikci_id=orm.tedarikci_id,
        ean=orm.ean,
        barkod=orm.barkod,
        ic_adet=orm.ic_adet,
        gramaj=orm.gramaj,
        birim=orm.birim,
        fiyat=orm.fiyat,
        min_stok=orm.min_stok,
        aciklama=orm.aciklama or "",
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
        stok_miktari=orm.stok_miktari if orm.stok_miktari is not None else 0,
    )


def urun_to_orm(entity: Urun) -> UrunORM:
    return UrunORM(
        id=entity.id,
        isim=entity.isim,
        marka_id=entity.marka_id,
        kategori_id=entity.kategori_id,
        tedarikci_id=entity.tedarikci_id,
        ean=entity.ean,
        barkod=entity.barkod,
        ic_adet=entity.ic_adet,
        gramaj=entity.gramaj,
        birim=entity.birim,
        fiyat=entity.fiyat,
        min_stok=entity.min_stok,
        aciklama=entity.aciklama,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
    )


def stok_hareketi_to_entity(orm: StokHareketiORM) -> StokHareketi:
    return StokHareketi(
        id=orm.id,
        urun_id=orm.urun_id,
        lot_id=orm.lot_id,
        palet_id=orm.palet_id,
        raf_id=orm.raf_id,
        hareket_tipi=orm.hareket_tipi,
        miktar=orm.miktar,
        siparis_no=orm.siparis_no,
        irsaliye_no=orm.irsaliye_no,
        tir_plaka=orm.tir_plaka,
        depo_kapi=orm.depo_kapi,
        barkodlar=orm.barkodlar,
        aciklama=orm.aciklama or "",
        kullanici_id=orm.kullanici_id,
        tarih=orm.tarih,
        palet_no=orm.palet.palet_no if orm.palet else None,
    )


def stok_hareketi_to_orm(entity: StokHareketi) -> StokHareketiORM:
    return StokHareketiORM(
        id=entity.id,
        urun_id=entity.urun_id,
        lot_id=entity.lot_id,
        palet_id=entity.palet_id,
        raf_id=entity.raf_id,
        hareket_tipi=entity.hareket_tipi,
        miktar=entity.miktar,
        siparis_no=entity.siparis_no,
        irsaliye_no=entity.irsaliye_no,
        tir_plaka=entity.tir_plaka,
        depo_kapi=entity.depo_kapi,
        barkodlar=entity.barkodlar,
        aciklama=entity.aciklama,
        kullanici_id=entity.kullanici_id,
        tarih=entity.tarih,
    )
