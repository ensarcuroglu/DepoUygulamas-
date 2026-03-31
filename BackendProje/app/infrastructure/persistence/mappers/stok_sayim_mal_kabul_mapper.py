"""Stok sayım & mal kabul domain mapper'ları — StokSayim, StokSayimKalemi, MalKabulIrsaliye, MalKabulKalemi."""

from __future__ import annotations

from models import (
    StokSayim as StokSayimORM,
    StokSayimKalemi as StokSayimKalemiORM,
    MalKabulIrsaliye as MalKabulIrsaliyeORM,
    MalKabulKalemi as MalKabulKalemiORM,
)
from app.core.entities.stok_sayim import StokSayim, StokSayimKalemi
from app.core.entities.mal_kabul_irsaliye import MalKabulIrsaliye, MalKabulKalemi


def stok_sayim_kalemi_to_entity(orm: StokSayimKalemiORM) -> StokSayimKalemi:
    return StokSayimKalemi(
        id=orm.id,
        sayim_id=orm.sayim_id,
        urun_id=orm.urun_id,
        sayilan_miktar=orm.sayilan_miktar,
        notlar=orm.notlar or "",
        user_id=orm.user_id,
        sayim_tarihi=orm.sayim_tarihi,
    )


def stok_sayim_kalemi_to_orm(entity: StokSayimKalemi) -> StokSayimKalemiORM:
    return StokSayimKalemiORM(
        id=entity.id,
        sayim_id=entity.sayim_id,
        urun_id=entity.urun_id,
        sayilan_miktar=entity.sayilan_miktar,
        notlar=entity.notlar,
        user_id=entity.user_id,
        sayim_tarihi=entity.sayim_tarihi,
    )


def stok_sayim_to_entity(orm: StokSayimORM, kalemler_dahil: bool = True) -> StokSayim:
    kalemler: list[StokSayimKalemi] = []
    if kalemler_dahil:
        try:
            kalemler = [stok_sayim_kalemi_to_entity(k) for k in orm.sayim_kalemleri]
        except AttributeError:
            pass

    return StokSayim(
        id=orm.id,
        sayim_no=orm.sayim_no,
        aciklama=orm.aciklama or "",
        baslangic_tarihi=orm.baslangic_tarihi,
        bitis_tarihi=orm.bitis_tarihi,
        referans_stok_json=orm.referans_stok_json,
        kontrol_eden_user_id=orm.kontrol_eden_user_id,
        onaylayan_user_id=orm.onaylayan_user_id,
        durum=orm.durum,
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
        sayim_kalemleri=kalemler,
    )


def stok_sayim_to_orm(entity: StokSayim) -> StokSayimORM:
    return StokSayimORM(
        id=entity.id,
        sayim_no=entity.sayim_no,
        aciklama=entity.aciklama,
        baslangic_tarihi=entity.baslangic_tarihi,
        bitis_tarihi=entity.bitis_tarihi,
        referans_stok_json=entity.referans_stok_json,
        kontrol_eden_user_id=entity.kontrol_eden_user_id,
        onaylayan_user_id=entity.onaylayan_user_id,
        durum=entity.durum,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def mal_kabul_kalemi_to_entity(orm: MalKabulKalemiORM) -> MalKabulKalemi:
    return MalKabulKalemi(
        id=orm.id,
        mal_kabul_irsaliyesi_id=orm.mal_kabul_irsaliyesi_id,
        palet_no=orm.palet_no,
        urun_id=orm.urun_id,
        lot_no=orm.lot_no,
        miktar=orm.miktar,
        raf_id=orm.raf_id,
        durum=orm.durum,
        uretim_tarihi=orm.uretim_tarihi,
        son_kullanma_tarihi=orm.son_kullanma_tarihi,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def mal_kabul_kalemi_to_orm(entity: MalKabulKalemi) -> MalKabulKalemiORM:
    return MalKabulKalemiORM(
        id=entity.id,
        mal_kabul_irsaliyesi_id=entity.mal_kabul_irsaliyesi_id,
        palet_no=entity.palet_no,
        urun_id=entity.urun_id,
        lot_no=entity.lot_no,
        miktar=entity.miktar,
        raf_id=entity.raf_id,
        durum=entity.durum,
        uretim_tarihi=entity.uretim_tarihi,
        son_kullanma_tarihi=entity.son_kullanma_tarihi,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def mal_kabul_irsaliye_to_entity(
    orm: MalKabulIrsaliyeORM, kalemler_dahil: bool = True,
) -> MalKabulIrsaliye:
    kalemler: list[MalKabulKalemi] = []
    if kalemler_dahil:
        kalemler = [mal_kabul_kalemi_to_entity(k) for k in orm.kalemler]
    return MalKabulIrsaliye(
        id=orm.id,
        irsaliye_no=orm.irsaliye_no,
        tedarikci_id=orm.tedarikci_id,
        depo_id=orm.depo_id,
        tir_plaka=orm.tir_plaka,
        sofor_adi=orm.sofor_adi,
        durum=orm.durum,
        tarih=orm.tarih,
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
        kalemler=kalemler,
    )


def mal_kabul_irsaliye_to_orm(entity: MalKabulIrsaliye) -> MalKabulIrsaliyeORM:
    orm = MalKabulIrsaliyeORM(
        id=entity.id,
        irsaliye_no=entity.irsaliye_no,
        tedarikci_id=entity.tedarikci_id,
        depo_id=entity.depo_id,
        tir_plaka=entity.tir_plaka,
        sofor_adi=entity.sofor_adi,
        durum=entity.durum,
        tarih=entity.tarih,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
    )
    for kalem_entity in entity.kalemler:
        orm.kalemler.append(mal_kabul_kalemi_to_orm(kalem_entity))
    return orm
