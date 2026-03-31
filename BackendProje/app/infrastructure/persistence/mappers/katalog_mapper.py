"""Katalog domain mapper'ları — Marka, Kategori, Tedarikci."""

from __future__ import annotations

from models import (
    Marka as MarkaORM,
    Kategori as KategoriORM,
    Tedarikci as TedarikciORM,
)
from app.core.entities.marka import Marka
from app.core.entities.kategori import Kategori
from app.core.entities.tedarikci import Tedarikci


def marka_to_entity(orm: MarkaORM) -> Marka:
    return Marka(
        id=orm.id,
        isim=orm.isim,
        aciklama=orm.aciklama or "",
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def marka_to_orm(entity: Marka) -> MarkaORM:
    return MarkaORM(
        id=entity.id,
        isim=entity.isim,
        aciklama=entity.aciklama,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def kategori_to_entity(orm: KategoriORM) -> Kategori:
    return Kategori(
        id=orm.id,
        isim=orm.isim,
        aciklama=orm.aciklama or "",
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def kategori_to_orm(entity: Kategori) -> KategoriORM:
    return KategoriORM(
        id=entity.id,
        isim=entity.isim,
        aciklama=entity.aciklama,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def tedarikci_to_entity(orm: TedarikciORM) -> Tedarikci:
    return Tedarikci(
        id=orm.id,
        firma_adi=orm.firma_adi,
        iletisim_kisi=orm.iletisim_kisi,
        telefon=orm.telefon,
        email=orm.email,
        adres=orm.adres,
        vergi_no=orm.vergi_no,
        aktif=orm.aktif,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def tedarikci_to_orm(entity: Tedarikci) -> TedarikciORM:
    return TedarikciORM(
        id=entity.id,
        firma_adi=entity.firma_adi,
        iletisim_kisi=entity.iletisim_kisi,
        telefon=entity.telefon,
        email=entity.email,
        adres=entity.adres,
        vergi_no=entity.vergi_no,
        aktif=entity.aktif,
        olusturma_tarihi=entity.olusturma_tarihi,
    )
