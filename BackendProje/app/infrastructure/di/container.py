"""
Dependency Injection Container — FastAPI Depends tabanlı.

Core repository arayüzlerini Infrastructure'daki somut SQLAlchemy
implementasyonlarına bağlar ve Use Case'leri enjekte eder.

Kullanım (router'dan):
    from app.infrastructure.di.container import get_urun_listele_uc
    @router.get("/")
    def listele(uc = Depends(get_urun_listele_uc)):
        return uc.execute(...)
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db

# ── SQLAlchemy repository implementasyonları ──
from app.infrastructure.persistence.repositories import (
    SqlAlchemyUrunRepository,
    SqlAlchemyLotRepository,
    SqlAlchemyPaletRepository,
    SqlAlchemyStokHareketiRepository,
    SqlAlchemySistemLogRepository,
    SqlAlchemySiparisRepository,
    SqlAlchemyMarkaRepository,
    SqlAlchemyKategoriRepository,
    SqlAlchemyTedarikciRepository,
    SqlAlchemyDepoRepository,
    SqlAlchemyRafRepository,
    SqlAlchemyKullaniciRepository,
    SqlAlchemyDestekTalebiRepository,
    SqlAlchemyIrsaliyeRepository,
    SqlAlchemySevkiyatPlaniRepository,
    SqlAlchemyStokSayimRepository,
    SqlAlchemyRaporSablonuRepository,
    SqlAlchemyRaporLoguRepository,
    SqlAlchemyRaporScheduleRepository,
    SqlAlchemyRaporVeriRepository,
    SqlAlchemyDashboardRepository,
    SqlAlchemyMalKabulIrsaliyeRepository,
)

# ── Use Case sınıfları ──
from app.application.use_cases import (
    # Ürün
    UrunListeleUseCase,
    UrunGetirUseCase,
    UrunOlusturUseCase,
    UrunGuncelleUseCase,
    UrunSilUseCase,
    KritikUrunleriGetirUseCase,
    # Stok Hareketi
    StokHareketiListeleUseCase,
    StokHareketiOlusturUseCase,
    # Sipariş
    SiparisListeleUseCase,
    SiparisGetirUseCase,
    SiparisOlusturUseCase,
    SiparisGuncelleUseCase,
    SiparisSilUseCase,
    # Marka
    MarkaListeleUseCase,
    MarkaGetirUseCase,
    MarkaOlusturUseCase,
    MarkaGuncelleUseCase,
    MarkaSilUseCase,
    # Kategori
    KategoriListeleUseCase,
    KategoriGetirUseCase,
    KategoriOlusturUseCase,
    KategoriGuncelleUseCase,
    KategoriSilUseCase,
    # Tedarikçi
    TedarikciListeleUseCase,
    TedarikciGetirUseCase,
    TedarikciOlusturUseCase,
    TedarikciGuncelleUseCase,
    TedarikciSilUseCase,
    # Depo
    DepoListeleUseCase,
    DepoGetirUseCase,
    DepoOlusturUseCase,
    DepoGuncelleUseCase,
    DepoSilUseCase,
    # Raf
    RafListeleUseCase,
    RafGetirUseCase,
    RafOlusturUseCase,
    RafGuncelleUseCase,
    RafSilUseCase,
    # Lot
    LotListeleUseCase,
    LotGetirUseCase,
    LotSktYaklasanUseCase,
    LotOlusturUseCase,
    LotGuncelleUseCase,
    LotSilUseCase,
    # Palet
    PaletListeleUseCase,
    PaletGetirUseCase,
    PaletBarkodIleGetirUseCase,
    PaletSonrakiNumaraUseCase,
    PaletOlusturUseCase,
    PaletGuncelleUseCase,
    PaletSilUseCase,
    # Kullanıcı
    KullaniciListeleUseCase,
    KullaniciGetirUseCase,
    KullaniciGuncelleUseCase,
    KullaniciSilUseCase,
    # Destek Talebi
    DestekTalebiListeleUseCase,
    DestekTalebiGetirUseCase,
    DestekTalebiOlusturUseCase,
    DestekTalebiGuncelleUseCase,
    # Sistem Log
    SistemLogListeleUseCase,
    SistemLogOlusturUseCase,
    # İrsaliye
    IrsaliyeListeleUseCase,
    IrsaliyeGetirUseCase,
    IrsaliyeOlusturUseCase,
    IrsaliyeGuncelleUseCase,
    IrsaliyeYazdirVerisiGetirUseCase,
    # Sevkiyat Planı
    SevkiyatPlaniListeleUseCase,
    SevkiyatPlaniGetirUseCase,
    SevkiyatPlaniOlusturUseCase,
    SevkiyatPlaniGuncelleUseCase,
    SevkiyatPlaniSilUseCase,
    # Stok Sayım
    StokSayimListeleUseCase,
    StokSayimGetirUseCase,
    StokSayimBaslatUseCase,
    StokSayimKalemKaydetUseCase,
    StokSayimVaryansHesaplaUseCase,
    StokSayimOnaylaUseCase,
    # Rapor
    RaporSablonuListeleUseCase,
    RaporSablonuGetirUseCase,
    RaporSablonuOlusturUseCase,
    RaporSablonuGuncelleUseCase,
    RaporSablonuSilUseCase,
    RaporLoguListeleUseCase,
    RaporLoguYazUseCase,
    RaporScheduleListeleUseCase,
    RaporScheduleGetirUseCase,
    RaporScheduleOlusturUseCase,
    RaporScheduleGuncelleUseCase,
    RaporScheduleSilUseCase,
    RaporScheduleTetikleUseCase,
    RaporVeriSorgulaUseCase,
    RaporExportUseCase,
    # Mal Kabul İrsaliyesi
    MalKabulIrsaliyeListeleUseCase,
    MalKabulIrsaliyeGetirUseCase,
    MalKabulIrsaliyeOlusturUseCase,
    MalKabulIrsaliyeGuncelleUseCase,
    MalKabulIrsaliyeSilUseCase,
)
from app.application.use_cases.dashboard_use_cases import DashboardIstatistikGetirUseCase

# ── Domain Service ──
from app.core.services.stok_cikis_domain_service import StokCikisDomainService
from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService

# ── Palet Veri Kaynagi Adapter + Sorgulama ──
from app.infrastructure.services.irsaliye_palet_veri_kaynagi_service import IrsaliyePaletVeriKaynagiService
from app.infrastructure.services.palet_sorgulama_service import PaletSorgulamaService

# ── Şifre hash fonksiyonu (Kullanıcı use case'i için) ──
from app.core.auth import get_password_hash


# ═══════════════════════════════════════════════════════════════
# REPOSITORY FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_urun_repo(db: Session = Depends(get_db)):
    return SqlAlchemyUrunRepository(db)


def get_lot_repo(db: Session = Depends(get_db)):
    return SqlAlchemyLotRepository(db)


def get_palet_repo(db: Session = Depends(get_db)):
    return SqlAlchemyPaletRepository(db)


def get_hareket_repo(db: Session = Depends(get_db)):
    return SqlAlchemyStokHareketiRepository(db)


def get_log_repo(db: Session = Depends(get_db)):
    return SqlAlchemySistemLogRepository(db)


def get_siparis_repo(db: Session = Depends(get_db)):
    return SqlAlchemySiparisRepository(db)


def get_marka_repo(db: Session = Depends(get_db)):
    return SqlAlchemyMarkaRepository(db)


def get_kategori_repo(db: Session = Depends(get_db)):
    return SqlAlchemyKategoriRepository(db)


def get_tedarikci_repo(db: Session = Depends(get_db)):
    return SqlAlchemyTedarikciRepository(db)


def get_depo_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDepoRepository(db)


def get_raf_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRafRepository(db)


def get_kullanici_repo(db: Session = Depends(get_db)):
    return SqlAlchemyKullaniciRepository(db)


def get_destek_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDestekTalebiRepository(db)


def get_irsaliye_repo(db: Session = Depends(get_db)):
    return SqlAlchemyIrsaliyeRepository(db)


def get_sevkiyat_repo(db: Session = Depends(get_db)):
    return SqlAlchemySevkiyatPlaniRepository(db)


def get_stok_sayim_repo(db: Session = Depends(get_db)):
    return SqlAlchemyStokSayimRepository(db)


# ═══════════════════════════════════════════════════════════════
# ÜRÜN USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_urun_listele_uc(
    urun_repo=Depends(get_urun_repo),
):
    return UrunListeleUseCase(urun_repo)


def get_urun_getir_uc(
    urun_repo=Depends(get_urun_repo),
):
    return UrunGetirUseCase(urun_repo)


def get_kritik_urunler_uc(
    urun_repo=Depends(get_urun_repo),
):
    return KritikUrunleriGetirUseCase(urun_repo)


def get_urun_olustur_uc(
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return UrunOlusturUseCase(urun_repo, log_repo)


def get_urun_guncelle_uc(
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return UrunGuncelleUseCase(urun_repo, log_repo)


def get_urun_sil_uc(
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return UrunSilUseCase(urun_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# STOK HAREKETİ USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_stok_hareketi_listele_uc(
    hareket_repo=Depends(get_hareket_repo),
):
    return StokHareketiListeleUseCase(hareket_repo)


def get_stok_hareketi_olustur_uc(
    db: Session = Depends(get_db),
    urun_repo=Depends(get_urun_repo),
    lot_repo=Depends(get_lot_repo),
    palet_repo=Depends(get_palet_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return StokHareketiOlusturUseCase(
        urun_repo, lot_repo, palet_repo, hareket_repo, log_repo, db
    )


# ═══════════════════════════════════════════════════════════════
# SİPARİŞ USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_siparis_listele_uc(
    siparis_repo=Depends(get_siparis_repo),
):
    return SiparisListeleUseCase(siparis_repo)


def get_siparis_getir_uc(
    siparis_repo=Depends(get_siparis_repo),
):
    return SiparisGetirUseCase(siparis_repo)


def get_siparis_olustur_uc(
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
):
    return SiparisOlusturUseCase(siparis_repo, log_repo)


def get_siparis_guncelle_uc(
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
):
    return SiparisGuncelleUseCase(siparis_repo, log_repo)


def get_siparis_sil_uc(
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
):
    return SiparisSilUseCase(siparis_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# MARKA USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_marka_listele_uc(
    marka_repo=Depends(get_marka_repo),
):
    return MarkaListeleUseCase(marka_repo)


def get_marka_getir_uc(
    marka_repo=Depends(get_marka_repo),
):
    return MarkaGetirUseCase(marka_repo)


def get_marka_olustur_uc(
    marka_repo=Depends(get_marka_repo),
    log_repo=Depends(get_log_repo),
):
    return MarkaOlusturUseCase(marka_repo, log_repo)


def get_marka_guncelle_uc(
    marka_repo=Depends(get_marka_repo),
    log_repo=Depends(get_log_repo),
):
    return MarkaGuncelleUseCase(marka_repo, log_repo)


def get_marka_sil_uc(
    marka_repo=Depends(get_marka_repo),
    log_repo=Depends(get_log_repo),
):
    return MarkaSilUseCase(marka_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# KATEGORİ USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_kategori_listele_uc(
    kategori_repo=Depends(get_kategori_repo),
):
    return KategoriListeleUseCase(kategori_repo)


def get_kategori_getir_uc(
    kategori_repo=Depends(get_kategori_repo),
):
    return KategoriGetirUseCase(kategori_repo)


def get_kategori_olustur_uc(
    kategori_repo=Depends(get_kategori_repo),
    log_repo=Depends(get_log_repo),
):
    return KategoriOlusturUseCase(kategori_repo, log_repo)


def get_kategori_guncelle_uc(
    kategori_repo=Depends(get_kategori_repo),
    log_repo=Depends(get_log_repo),
):
    return KategoriGuncelleUseCase(kategori_repo, log_repo)


def get_kategori_sil_uc(
    kategori_repo=Depends(get_kategori_repo),
    log_repo=Depends(get_log_repo),
):
    return KategoriSilUseCase(kategori_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# TEDARİKÇİ USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_tedarikci_listele_uc(
    tedarikci_repo=Depends(get_tedarikci_repo),
):
    return TedarikciListeleUseCase(tedarikci_repo)


def get_tedarikci_getir_uc(
    tedarikci_repo=Depends(get_tedarikci_repo),
):
    return TedarikciGetirUseCase(tedarikci_repo)


def get_tedarikci_olustur_uc(
    tedarikci_repo=Depends(get_tedarikci_repo),
    log_repo=Depends(get_log_repo),
):
    return TedarikciOlusturUseCase(tedarikci_repo, log_repo)


def get_tedarikci_guncelle_uc(
    tedarikci_repo=Depends(get_tedarikci_repo),
    log_repo=Depends(get_log_repo),
):
    return TedarikciGuncelleUseCase(tedarikci_repo, log_repo)


def get_tedarikci_sil_uc(
    tedarikci_repo=Depends(get_tedarikci_repo),
    log_repo=Depends(get_log_repo),
):
    return TedarikciSilUseCase(tedarikci_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# DEPO USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_depo_listele_uc(
    depo_repo=Depends(get_depo_repo),
):
    return DepoListeleUseCase(depo_repo)


def get_depo_getir_uc(
    depo_repo=Depends(get_depo_repo),
):
    return DepoGetirUseCase(depo_repo)


def get_depo_olustur_uc(
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return DepoOlusturUseCase(depo_repo, log_repo)


def get_depo_guncelle_uc(
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return DepoGuncelleUseCase(depo_repo, log_repo)


def get_depo_sil_uc(
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return DepoSilUseCase(depo_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# RAF USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_raf_listele_uc(
    raf_repo=Depends(get_raf_repo),
):
    return RafListeleUseCase(raf_repo)


def get_raf_getir_uc(
    raf_repo=Depends(get_raf_repo),
):
    return RafGetirUseCase(raf_repo)


def get_raf_olustur_uc(
    raf_repo=Depends(get_raf_repo),
    depo_repo=Depends(get_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return RafOlusturUseCase(raf_repo, depo_repo, log_repo)


def get_raf_guncelle_uc(
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return RafGuncelleUseCase(raf_repo, log_repo)


def get_raf_sil_uc(
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return RafSilUseCase(raf_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# LOT USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_lot_listele_uc(
    lot_repo=Depends(get_lot_repo),
):
    return LotListeleUseCase(lot_repo)


def get_lot_getir_uc(
    lot_repo=Depends(get_lot_repo),
):
    return LotGetirUseCase(lot_repo)


def get_lot_skt_yaklasan_uc(
    lot_repo=Depends(get_lot_repo),
):
    return LotSktYaklasanUseCase(lot_repo)


def get_lot_olustur_uc(
    lot_repo=Depends(get_lot_repo),
    log_repo=Depends(get_log_repo),
):
    return LotOlusturUseCase(lot_repo, log_repo)


def get_lot_guncelle_uc(
    lot_repo=Depends(get_lot_repo),
    log_repo=Depends(get_log_repo),
):
    return LotGuncelleUseCase(lot_repo, log_repo)


def get_lot_sil_uc(
    lot_repo=Depends(get_lot_repo),
    log_repo=Depends(get_log_repo),
):
    return LotSilUseCase(lot_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# PALET USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_palet_listele_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletListeleUseCase(palet_repo)


def get_palet_getir_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletGetirUseCase(palet_repo)


def get_palet_barkod_ile_getir_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletBarkodIleGetirUseCase(palet_repo)


def get_palet_sonraki_numara_uc(
    palet_repo=Depends(get_palet_repo),
):
    return PaletSonrakiNumaraUseCase(palet_repo)


def get_palet_olustur_uc(
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    raf_repo=Depends(get_raf_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletOlusturUseCase(palet_repo, lot_repo, raf_repo, log_repo)


def get_palet_guncelle_uc(
    palet_repo=Depends(get_palet_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletGuncelleUseCase(palet_repo, log_repo)


def get_palet_sil_uc(
    palet_repo=Depends(get_palet_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletSilUseCase(palet_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# KULLANICI USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_kullanici_listele_uc(
    kullanici_repo=Depends(get_kullanici_repo),
):
    return KullaniciListeleUseCase(kullanici_repo)


def get_kullanici_getir_uc(
    kullanici_repo=Depends(get_kullanici_repo),
):
    return KullaniciGetirUseCase(kullanici_repo)


def get_kullanici_guncelle_uc(
    kullanici_repo=Depends(get_kullanici_repo),
    log_repo=Depends(get_log_repo),
):
    return KullaniciGuncelleUseCase(kullanici_repo, log_repo, password_hasher=get_password_hash)


def get_kullanici_sil_uc(
    kullanici_repo=Depends(get_kullanici_repo),
    log_repo=Depends(get_log_repo),
):
    return KullaniciSilUseCase(kullanici_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# DESTEK TALEBİ USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_destek_listele_uc(
    destek_repo=Depends(get_destek_repo),
):
    return DestekTalebiListeleUseCase(destek_repo)


def get_destek_getir_uc(
    destek_repo=Depends(get_destek_repo),
):
    return DestekTalebiGetirUseCase(destek_repo)


def get_destek_olustur_uc(
    destek_repo=Depends(get_destek_repo),
    log_repo=Depends(get_log_repo),
):
    return DestekTalebiOlusturUseCase(destek_repo, log_repo)


def get_destek_guncelle_uc(
    destek_repo=Depends(get_destek_repo),
    log_repo=Depends(get_log_repo),
):
    return DestekTalebiGuncelleUseCase(destek_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# SİSTEM LOG USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_sistem_log_listele_uc(
    log_repo=Depends(get_log_repo),
):
    return SistemLogListeleUseCase(log_repo)


def get_sistem_log_olustur_uc(
    log_repo=Depends(get_log_repo),
):
    return SistemLogOlusturUseCase(log_repo)


# ═══════════════════════════════════════════════════════════════
# STOK ÇIKIŞ DOMAİN SERVİSİ FACTORY
# ═══════════════════════════════════════════════════════════════

def get_stok_cikis_service(
    palet_repo=Depends(get_palet_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return StokCikisDomainService(palet_repo, hareket_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# İRSALİYE USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_irsaliye_listele_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
):
    return IrsaliyeListeleUseCase(irsaliye_repo)


def get_irsaliye_getir_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
):
    return IrsaliyeGetirUseCase(irsaliye_repo)


def get_irsaliye_olustur_uc(
    db: Session = Depends(get_db),
    irsaliye_repo=Depends(get_irsaliye_repo),
    siparis_repo=Depends(get_siparis_repo),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    log_repo=Depends(get_log_repo),
    stok_cikis_service=Depends(get_stok_cikis_service),
):
    return IrsaliyeOlusturUseCase(
        irsaliye_repo, siparis_repo, sevkiyat_repo, log_repo, stok_cikis_service, db
    )


def get_irsaliye_guncelle_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
    log_repo=Depends(get_log_repo),
):
    return IrsaliyeGuncelleUseCase(irsaliye_repo, log_repo)


def get_irsaliye_yazdir_uc(
    irsaliye_repo=Depends(get_irsaliye_repo),
    siparis_repo=Depends(get_siparis_repo),
):
    return IrsaliyeYazdirVerisiGetirUseCase(irsaliye_repo, siparis_repo)


# ═══════════════════════════════════════════════════════════════
# SEVKIYAT PLANI USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_sevkiyat_listele_uc(
    sevkiyat_repo=Depends(get_sevkiyat_repo),
):
    return SevkiyatPlaniListeleUseCase(sevkiyat_repo)


def get_sevkiyat_getir_uc(
    sevkiyat_repo=Depends(get_sevkiyat_repo),
):
    return SevkiyatPlaniGetirUseCase(sevkiyat_repo)


def get_sevkiyat_olustur_uc(
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
):
    return SevkiyatPlaniOlusturUseCase(sevkiyat_repo, siparis_repo, log_repo)


def get_sevkiyat_guncelle_uc(
    db: Session = Depends(get_db),
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    siparis_repo=Depends(get_siparis_repo),
    log_repo=Depends(get_log_repo),
    stok_cikis_service=Depends(get_stok_cikis_service),
):
    return SevkiyatPlaniGuncelleUseCase(sevkiyat_repo, siparis_repo, log_repo, stok_cikis_service, db)


def get_sevkiyat_sil_uc(
    sevkiyat_repo=Depends(get_sevkiyat_repo),
    log_repo=Depends(get_log_repo),
):
    return SevkiyatPlaniSilUseCase(sevkiyat_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# STOK SAYIM USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_stok_sayim_listele_uc(
    sayim_repo=Depends(get_stok_sayim_repo),
):
    return StokSayimListeleUseCase(sayim_repo)


def get_stok_sayim_getir_uc(
    sayim_repo=Depends(get_stok_sayim_repo),
):
    return StokSayimGetirUseCase(sayim_repo)


def get_stok_sayim_baslat_uc(
    sayim_repo=Depends(get_stok_sayim_repo),
    log_repo=Depends(get_log_repo),
):
    return StokSayimBaslatUseCase(sayim_repo, log_repo)


def get_stok_sayim_kalem_kaydet_uc(
    sayim_repo=Depends(get_stok_sayim_repo),
    urun_repo=Depends(get_urun_repo),
):
    return StokSayimKalemKaydetUseCase(sayim_repo, urun_repo)


def get_stok_sayim_varyans_uc(
    sayim_repo=Depends(get_stok_sayim_repo),
    urun_repo=Depends(get_urun_repo),
):
    return StokSayimVaryansHesaplaUseCase(sayim_repo, urun_repo)


def get_stok_sayim_onayla_uc(
    sayim_repo=Depends(get_stok_sayim_repo),
    log_repo=Depends(get_log_repo),
):
    return StokSayimOnaylaUseCase(sayim_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# RAPOR REPOSITORY FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_rapor_sablon_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporSablonuRepository(db)


def get_rapor_log_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporLoguRepository(db)


def get_rapor_schedule_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporScheduleRepository(db)


def get_rapor_veri_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporVeriRepository(db)


# ═══════════════════════════════════════════════════════════════
# RAPOR ŞABLONU USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_rapor_sablon_listele_uc(
    sablon_repo=Depends(get_rapor_sablon_repo),
):
    return RaporSablonuListeleUseCase(sablon_repo)


def get_rapor_sablon_getir_uc(
    sablon_repo=Depends(get_rapor_sablon_repo),
):
    return RaporSablonuGetirUseCase(sablon_repo)


def get_rapor_sablon_olustur_uc(
    sablon_repo=Depends(get_rapor_sablon_repo),
    log_repo=Depends(get_log_repo),
):
    return RaporSablonuOlusturUseCase(sablon_repo, log_repo)


def get_rapor_sablon_guncelle_uc(
    sablon_repo=Depends(get_rapor_sablon_repo),
    log_repo=Depends(get_log_repo),
):
    return RaporSablonuGuncelleUseCase(sablon_repo, log_repo)


def get_rapor_sablon_sil_uc(
    sablon_repo=Depends(get_rapor_sablon_repo),
    log_repo=Depends(get_log_repo),
):
    return RaporSablonuSilUseCase(sablon_repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# RAPOR LOGU USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_rapor_logu_listele_uc(
    rapor_log_repo=Depends(get_rapor_log_repo),
):
    return RaporLoguListeleUseCase(rapor_log_repo)


def get_rapor_logu_yaz_uc(
    rapor_log_repo=Depends(get_rapor_log_repo),
):
    return RaporLoguYazUseCase(rapor_log_repo)


# ═══════════════════════════════════════════════════════════════
# RAPOR SCHEDULE USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_rapor_schedule_listele_uc(
    schedule_repo=Depends(get_rapor_schedule_repo),
):
    return RaporScheduleListeleUseCase(schedule_repo)


def get_rapor_schedule_getir_uc(
    schedule_repo=Depends(get_rapor_schedule_repo),
):
    return RaporScheduleGetirUseCase(schedule_repo)


def get_rapor_schedule_olustur_uc(
    schedule_repo=Depends(get_rapor_schedule_repo),
    log_repo=Depends(get_log_repo),
):
    return RaporScheduleOlusturUseCase(schedule_repo, log_repo)


def get_rapor_schedule_guncelle_uc(
    schedule_repo=Depends(get_rapor_schedule_repo),
    log_repo=Depends(get_log_repo),
):
    return RaporScheduleGuncelleUseCase(schedule_repo, log_repo)


def get_rapor_schedule_sil_uc(
    schedule_repo=Depends(get_rapor_schedule_repo),
    log_repo=Depends(get_log_repo),
):
    return RaporScheduleSilUseCase(schedule_repo, log_repo)


def get_rapor_schedule_tetikle_uc(
    schedule_repo=Depends(get_rapor_schedule_repo),
    rapor_log_repo=Depends(get_rapor_log_repo),
):
    return RaporScheduleTetikleUseCase(schedule_repo, rapor_log_repo)


# ═══════════════════════════════════════════════════════════════
# RAPOR VERİ + EXPORT USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_rapor_veri_sorgula_uc(
    veri_repo=Depends(get_rapor_veri_repo),
    rapor_log_repo=Depends(get_rapor_log_repo),
):
    return RaporVeriSorgulaUseCase(veri_repo, rapor_log_repo)


def get_rapor_export_uc(
    veri_repo=Depends(get_rapor_veri_repo),
    rapor_log_repo=Depends(get_rapor_log_repo),
):
    return RaporExportUseCase(veri_repo, rapor_log_repo)


# ═══════════════════════════════════════════════════════════════
# DASHBOARD REPOSITORY + USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_dashboard_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDashboardRepository(db)


def get_dashboard_istatistik_uc(
    dashboard_repo=Depends(get_dashboard_repo),
):
    return DashboardIstatistikGetirUseCase(dashboard_repo)


# ═══════════════════════════════════════════════════════════════
# MAL KABUL İRSALİYESİ REPOSITORY + USE CASE FACTORY'LERİ
# ═══════════════════════════════════════════════════════════════

def get_mal_kabul_irsaliye_repo(db: Session = Depends(get_db)):
    return SqlAlchemyMalKabulIrsaliyeRepository(db)


def get_mal_kabul_irsaliye_listele_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
):
    return MalKabulIrsaliyeListeleUseCase(repo)


def get_mal_kabul_irsaliye_getir_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
):
    return MalKabulIrsaliyeGetirUseCase(repo)


def get_mal_kabul_irsaliye_olustur_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
    tedarikci_repo=Depends(get_tedarikci_repo),
    depo_repo=Depends(get_depo_repo),
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return MalKabulIrsaliyeOlusturUseCase(repo, tedarikci_repo, depo_repo, urun_repo, log_repo)


def get_mal_kabul_irsaliye_guncelle_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
    urun_repo=Depends(get_urun_repo),
    log_repo=Depends(get_log_repo),
):
    return MalKabulIrsaliyeGuncelleUseCase(repo, urun_repo, log_repo)


def get_mal_kabul_irsaliye_sil_uc(
    repo=Depends(get_mal_kabul_irsaliye_repo),
    log_repo=Depends(get_log_repo),
):
    return MalKabulIrsaliyeSilUseCase(repo, log_repo)


# ═══════════════════════════════════════════════════════════════
# PALET BAZLI STOK İŞLEMLERİ — ADAPTER + DOMAIN SERVICE
# ════════════════════════════════════════════════════════��══════

# -- Config-driven adapter secimi --
from app.infrastructure.config.erp_config import ErpConfig, PaletVeriKaynagi

_erp_config = ErpConfig.from_env()
_mock_erp_adapter = None


def get_palet_veri_kaynagi(
    mal_kabul_repo=Depends(get_mal_kabul_irsaliye_repo),
    urun_repo=Depends(get_urun_repo),
    depo_repo=Depends(get_depo_repo),
    raf_repo=Depends(get_raf_repo),
    lot_repo=Depends(get_lot_repo),
):
    """PALET_VERI_KAYNAGI env degiskenine gore adapter doner.

    LOCAL → IrsaliyePaletVeriKaynagiService (varsayilan)
    MOCK  → MockErpPaletVeriKaynagiService (demo/dev)
    ERP   → ErpPaletVeriKaynagiService (gercek ERP)
    """
    global _mock_erp_adapter

    if _erp_config.palet_veri_kaynagi == PaletVeriKaynagi.MOCK:
        if _mock_erp_adapter is None:
            from app.infrastructure.services.mock_erp_palet_veri_kaynagi_service import (
                MockErpPaletVeriKaynagiService,
            )
            _mock_erp_adapter = MockErpPaletVeriKaynagiService()
        return _mock_erp_adapter

    if _erp_config.palet_veri_kaynagi == PaletVeriKaynagi.ERP:
        from app.infrastructure.services.erp_palet_veri_kaynagi_service import (
            ErpPaletVeriKaynagiService,
        )
        return ErpPaletVeriKaynagiService(_erp_config)

    # LOCAL (varsayilan)
    return IrsaliyePaletVeriKaynagiService(
        mal_kabul_repo, urun_repo, depo_repo, raf_repo, lot_repo,
    )


def get_palet_bazli_stok_service(
    veri_kaynagi=Depends(get_palet_veri_kaynagi),
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    raf_repo=Depends(get_raf_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return PaletBazliStokDomainService(
        veri_kaynagi, palet_repo, lot_repo, raf_repo, hareket_repo, log_repo,
    )


def get_palet_sorgulama_service(
    veri_kaynagi=Depends(get_palet_veri_kaynagi),
    palet_repo=Depends(get_palet_repo),
    lot_repo=Depends(get_lot_repo),
    urun_repo=Depends(get_urun_repo),
    depo_repo=Depends(get_depo_repo),
    raf_repo=Depends(get_raf_repo),
):
    return PaletSorgulamaService(
        veri_kaynagi, palet_repo, lot_repo, urun_repo, depo_repo, raf_repo,
    )
