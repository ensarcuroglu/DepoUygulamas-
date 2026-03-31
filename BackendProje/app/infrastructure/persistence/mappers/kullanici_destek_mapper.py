"""Kullanıcı & destek domain mapper'ları — Kullanici, SistemLog, DestekTalebi."""

from __future__ import annotations

from models import (
    Kullanici as KullaniciORM,
    SistemLog as SistemLogORM,
    DestekTalebi as DestekTalebiORM,
)
from app.core.entities.kullanici import Kullanici
from app.core.entities.sistem_log import SistemLog
from app.core.entities.destek_talebi import DestekTalebi


def kullanici_to_entity(orm: KullaniciORM) -> Kullanici:
    return Kullanici(
        id=orm.id,
        kullanici_adi=orm.kullanici_adi,
        sifre_hash=orm.sifre_hash,
        ad_soyad=orm.ad_soyad,
        rol=orm.rol,
        telefon=orm.telefon,
        email=orm.email,
        departman=orm.departman,
        sicil_no=orm.sicil_no,
        kart_numarasi=orm.kart_numarasi,
        depo_id=orm.depo_id,
        refresh_token_hash=orm.refresh_token_hash,
        refresh_token_son_kullanim=orm.refresh_token_son_kullanim,
        olusturma_tarihi=orm.olusturma_tarihi,
    )


def kullanici_to_orm(entity: Kullanici) -> KullaniciORM:
    return KullaniciORM(
        id=entity.id,
        kullanici_adi=entity.kullanici_adi,
        sifre_hash=entity.sifre_hash,
        ad_soyad=entity.ad_soyad,
        rol=entity.rol,
        telefon=entity.telefon,
        email=entity.email,
        departman=entity.departman,
        sicil_no=entity.sicil_no,
        kart_numarasi=entity.kart_numarasi,
        depo_id=entity.depo_id,
        refresh_token_hash=entity.refresh_token_hash,
        refresh_token_son_kullanim=entity.refresh_token_son_kullanim,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


def sistem_log_to_entity(orm: SistemLogORM) -> SistemLog:
    return SistemLog(
        id=orm.id,
        kullanici_id=orm.kullanici_id,
        islem_tipi=orm.islem_tipi,
        modul=orm.modul,
        detay=orm.detay,
        eski_veri=orm.eski_veri,
        yeni_veri=orm.yeni_veri,
        tarih=orm.tarih,
    )


def sistem_log_to_orm(entity: SistemLog) -> SistemLogORM:
    return SistemLogORM(
        id=entity.id,
        kullanici_id=entity.kullanici_id,
        islem_tipi=entity.islem_tipi,
        modul=entity.modul,
        detay=entity.detay,
        eski_veri=entity.eski_veri,
        yeni_veri=entity.yeni_veri,
        tarih=entity.tarih,
    )


def destek_talebi_to_entity(orm: DestekTalebiORM) -> DestekTalebi:
    return DestekTalebi(
        id=orm.id,
        kullanici_id=orm.kullanici_id,
        konu=orm.konu,
        kategori=orm.kategori,
        oncelik=orm.oncelik,
        durum=orm.durum,
        aciklama=orm.aciklama,
        admin_cevabi=orm.admin_cevabi,
        olusturma_tarihi=orm.olusturma_tarihi,
        guncelleme_tarihi=orm.guncelleme_tarihi,
    )


def destek_talebi_to_orm(entity: DestekTalebi) -> DestekTalebiORM:
    return DestekTalebiORM(
        id=entity.id,
        kullanici_id=entity.kullanici_id,
        konu=entity.konu,
        kategori=entity.kategori,
        oncelik=entity.oncelik,
        durum=entity.durum,
        aciklama=entity.aciklama,
        admin_cevabi=entity.admin_cevabi,
        olusturma_tarihi=entity.olusturma_tarihi,
        guncelleme_tarihi=entity.guncelleme_tarihi,
    )
