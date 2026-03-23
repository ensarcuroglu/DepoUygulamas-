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
)


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
