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

from app.infrastructure.persistence.database import get_db

# ── SQLAlchemy repository implementasyonları ──
from app.infrastructure.persistence.repositories import (
    SqlAlchemyUrunRepository,
    SqlAlchemyLotRepository,
    SqlAlchemyPaletRepository,
    SqlAlchemyStokHareketiRepository,
    SqlAlchemySistemLogRepository,
    SqlAlchemySiparisRepository,
)

# ── Use Case sınıfları ──
from app.application.use_cases import (
    UrunListeleUseCase,
    UrunGetirUseCase,
    UrunOlusturUseCase,
    UrunGuncelleUseCase,
    UrunSilUseCase,
    KritikUrunleriGetirUseCase,
    StokHareketiListeleUseCase,
    StokHareketiOlusturUseCase,
    SiparisListeleUseCase,
    SiparisGetirUseCase,
    SiparisOlusturUseCase,
    SiparisGuncelleUseCase,
    SiparisSilUseCase,
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
    urun_repo=Depends(get_urun_repo),
    lot_repo=Depends(get_lot_repo),
    palet_repo=Depends(get_palet_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return StokHareketiOlusturUseCase(
        urun_repo, lot_repo, palet_repo, hareket_repo, log_repo
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
