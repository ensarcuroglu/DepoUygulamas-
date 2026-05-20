"""Sipariş & lojistik domain mapper'ları — Siparis, SiparisKalemi, SevkiyatPlani, Irsaliye."""

from __future__ import annotations

from sqlalchemy.orm.exc import DetachedInstanceError

from models import (
    Siparis as SiparisORM,
    SiparisKalemi as SiparisKalemiORM,
    SevkiyatPlani as SevkiyatPlaniORM,
    SevkiyatKalemi as SevkiyatKalemiORM,
    Irsaliye as IrsaliyeORM,
)
from app.core.entities.siparis import Siparis, SiparisKalemi
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatKalemi
from app.core.entities.irsaliye import Irsaliye


def siparis_kalemi_to_entity(orm: SiparisKalemiORM) -> SiparisKalemi:
    return SiparisKalemi(
        id=orm.id,
        siparis_id=orm.siparis_id,
        urun_id=orm.urun_id,
        miktar=orm.miktar,
        birim_fiyat=orm.birim_fiyat,
        kdv_orani=orm.kdv_orani,
        toplam=orm.toplam,
    )


def siparis_kalemi_to_orm(entity: SiparisKalemi) -> SiparisKalemiORM:
    return SiparisKalemiORM(
        id=entity.id,
        siparis_id=entity.siparis_id,
        urun_id=entity.urun_id,
        miktar=entity.miktar,
        birim_fiyat=entity.birim_fiyat,
        kdv_orani=entity.kdv_orani,
        toplam=entity.toplam,
    )


def siparis_to_entity(orm: SiparisORM, kalemler_dahil: bool = True) -> Siparis:
    kalemler: list[SiparisKalemi] = []
    if kalemler_dahil:
        try:
            kalemler = [siparis_kalemi_to_entity(k) for k in orm.kalemler]
        except DetachedInstanceError:
            kalemler = []

    return Siparis(
        id=orm.id,
        siparis_no=orm.siparis_no,
        musteri_adi=orm.musteri_adi,
        teslimat_adresi=orm.teslimat_adresi,
        teslimat_tarihi=orm.teslimat_tarihi,
        durum=orm.durum,
        oncelik=getattr(orm, "oncelik", 5),
        top_miktar=orm.top_miktar,
        top_tutar=orm.top_tutar,
        notlar=orm.notlar or "",
        olusturan_kullanici_id=orm.olusturan_kullanici_id,
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
        aktif=orm.aktif,
        kalemler=kalemler,
    )


def siparis_to_orm(entity: Siparis) -> SiparisORM:
    orm = SiparisORM(
        id=entity.id,
        siparis_no=entity.siparis_no,
        musteri_adi=entity.musteri_adi,
        teslimat_adresi=entity.teslimat_adresi,
        teslimat_tarihi=entity.teslimat_tarihi,
        durum=entity.durum,
        oncelik=entity.oncelik,
        top_miktar=entity.top_miktar,
        top_tutar=entity.top_tutar,
        notlar=entity.notlar,
        olusturan_kullanici_id=entity.olusturan_kullanici_id,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
        aktif=entity.aktif,
    )
    for kalem_entity in entity.kalemler:
        orm.kalemler.append(siparis_kalemi_to_orm(kalem_entity))
    return orm


def sevkiyat_kalemi_to_entity(orm: SevkiyatKalemiORM) -> SevkiyatKalemi:
    return SevkiyatKalemi(
        id=orm.id,
        sevkiyat_id=orm.sevkiyat_id,
        siparis_kalemi_id=orm.siparis_kalemi_id,
        urun_id=orm.urun_id,
        miktar=orm.miktar,
    )


def sevkiyat_kalemi_to_orm(entity: SevkiyatKalemi) -> SevkiyatKalemiORM:
    return SevkiyatKalemiORM(
        id=entity.id,
        sevkiyat_id=entity.sevkiyat_id,
        siparis_kalemi_id=entity.siparis_kalemi_id,
        urun_id=entity.urun_id,
        miktar=entity.miktar,
    )


def sevkiyat_plani_to_entity(orm: SevkiyatPlaniORM) -> SevkiyatPlani:
    kalemler: list[SevkiyatKalemi] = []
    try:
        kalemler = [sevkiyat_kalemi_to_entity(k) for k in orm.kalemler]
    except DetachedInstanceError:
        kalemler = []

    return SevkiyatPlani(
        id=orm.id,
        siparis_id=orm.siparis_id,
        tir_plaka=orm.tir_plaka,
        sofor_adi=orm.sofor_adi,
        sofor_telefon=orm.sofor_telefon,
        depo_kapi=orm.depo_kapi,
        yukleme_tarihi=orm.yukleme_tarihi,
        cikis_saati=orm.cikis_saati,
        varis_saati=orm.varis_saati,
        durum=orm.durum,
        notlar=orm.notlar or "",
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
        kalemler=kalemler,
    )


def sevkiyat_plani_to_orm(entity: SevkiyatPlani) -> SevkiyatPlaniORM:
    return SevkiyatPlaniORM(
        id=entity.id,
        siparis_id=entity.siparis_id,
        tir_plaka=entity.tir_plaka,
        sofor_adi=entity.sofor_adi,
        sofor_telefon=entity.sofor_telefon,
        depo_kapi=entity.depo_kapi,
        yukleme_tarihi=entity.yukleme_tarihi,
        cikis_saati=entity.cikis_saati,
        varis_saati=entity.varis_saati,
        durum=entity.durum,
        notlar=entity.notlar,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
    )


def irsaliye_to_entity(orm: IrsaliyeORM) -> Irsaliye:
    return Irsaliye(
        id=orm.id,
        siparis_id=orm.siparis_id,
        sevkiyat_id=orm.sevkiyat_id,
        irsaliye_no=orm.irsaliye_no,
        irsaliye_tarihi=orm.irsaliye_tarihi,
        belge_turu=orm.belge_turu,
        tir_plaka=orm.tir_plaka,
        sofor_adi=orm.sofor_adi,
        durum=orm.durum,
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
    )


def irsaliye_to_orm(entity: Irsaliye) -> IrsaliyeORM:
    return IrsaliyeORM(
        id=entity.id,
        siparis_id=entity.siparis_id,
        sevkiyat_id=entity.sevkiyat_id,
        irsaliye_no=entity.irsaliye_no,
        irsaliye_tarihi=entity.irsaliye_tarihi,
        belge_turu=entity.belge_turu,
        tir_plaka=entity.tir_plaka,
        sofor_adi=entity.sofor_adi,
        durum=entity.durum,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
    )
