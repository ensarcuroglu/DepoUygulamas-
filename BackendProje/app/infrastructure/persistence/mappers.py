"""
ORM Model ↔ Domain Entity dönüşüm fonksiyonları.

Her fonksiyon çifti:
  - to_entity : SQLAlchemy ORM nesnesi → saf Python dataclass (domain entity)
  - to_orm    : Domain entity → SQLAlchemy ORM nesnesi (yeni kayıt oluştururken)
"""

from __future__ import annotations
from typing import Optional, List

# ORM modelleri (mevcut models.py)
from models import (
    Marka as MarkaORM,
    Kategori as KategoriORM,
    Depo as DepoORM,
    Raf as RafORM,
    Tedarikci as TedarikciORM,
    Urun as UrunORM,
    Lot as LotORM,
    Palet as PaletORM,
    StokHareketi as StokHareketiORM,
    Kullanici as KullaniciORM,
    SistemLog as SistemLogORM,
    DestekTalebi as DestekTalebiORM,
    Siparis as SiparisORM,
    SiparisKalemi as SiparisKalemiORM,
    SevkiyatPlani as SevkiyatPlaniORM,
    Irsaliye as IrsaliyeORM,
    RaporSablonu as RaporSablonuORM,
    RaporLogu as RaporLoguORM,
    RaporSchedule as RaporScheduleORM,
    StokSayim as StokSayimORM,
    StokSayimKalemi as StokSayimKalemiORM,
)

# Domain entity'leri
from app.core.entities.marka import Marka
from app.core.entities.kategori import Kategori
from app.core.entities.depo import Depo
from app.core.entities.raf import Raf
from app.core.entities.tedarikci import Tedarikci
from app.core.entities.urun import Urun
from app.core.entities.lot import Lot
from app.core.entities.palet import Palet
from app.core.entities.stok_hareketi import StokHareketi
from app.core.entities.kullanici import Kullanici
from app.core.entities.sistem_log import SistemLog
from app.core.entities.destek_talebi import DestekTalebi
from app.core.entities.siparis import Siparis, SiparisKalemi
from app.core.entities.sevkiyat_plani import SevkiyatPlani
from app.core.entities.irsaliye import Irsaliye
from app.core.entities.rapor import RaporSablonu, RaporLogu, RaporSchedule
from app.core.entities.stok_sayim import StokSayim, StokSayimKalemi


# ════════════════════════════════════════════
# MARKA
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# KATEGORİ
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# DEPO
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# RAF
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# TEDARİKÇİ
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# ÜRÜN
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# LOT
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# PALET
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# STOK HAREKETİ
# ════════════════════════════════════════════

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
        tir_plaka=orm.tir_plaka,
        depo_kapi=orm.depo_kapi,
        barkodlar=orm.barkodlar,
        aciklama=orm.aciklama or "",
        kullanici_id=orm.kullanici_id,
        tarih=orm.tarih,
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
        tir_plaka=entity.tir_plaka,
        depo_kapi=entity.depo_kapi,
        barkodlar=entity.barkodlar,
        aciklama=entity.aciklama,
        kullanici_id=entity.kullanici_id,
        tarih=entity.tarih,
    )


# ════════════════════════════════════════════
# KULLANICI
# ════════════════════════════════════════════

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
        refresh_token_hash=entity.refresh_token_hash,
        refresh_token_son_kullanim=entity.refresh_token_son_kullanim,
        olusturma_tarihi=entity.olusturma_tarihi,
    )


# ════════════════════════════════════════════
# SİSTEM LOG
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# DESTEK TALEBİ
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# SİPARİŞ & SİPARİŞ KALEMİ
# ════════════════════════════════════════════

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
    kalemler: List[SiparisKalemi] = []
    if kalemler_dahil:
        try:
            kalemler = [siparis_kalemi_to_entity(k) for k in orm.kalemler]
        except Exception:
            pass  # Lazy-load tetiklenmemişse boş bırak

    return Siparis(
        id=orm.id,
        siparis_no=orm.siparis_no,
        musteri_adi=orm.musteri_adi,
        teslimat_adresi=orm.teslimat_adresi,
        teslimat_tarihi=orm.teslimat_tarihi,
        durum=orm.durum,
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


# ════════════════════════════════════════════
# SEVKİYAT PLANI
# ════════════════════════════════════════════

def sevkiyat_plani_to_entity(orm: SevkiyatPlaniORM) -> SevkiyatPlani:
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


# ════════════════════════════════════════════
# İRSALİYE
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# RAPOR ŞABLONU
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# RAPOR LOGU
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# RAPOR SCHEDULE
# ════════════════════════════════════════════

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


# ════════════════════════════════════════════
# STOK SAYIM & KALEMİ
# ════════════════════════════════════════════

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
    kalemler: List[StokSayimKalemi] = []
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
    orm = StokSayimORM(
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
    return orm
