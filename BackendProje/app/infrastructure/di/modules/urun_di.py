"""DI — Ürün."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import SqlAlchemyUrunRepository
from app.application.use_cases import (
    UrunListeleUseCase,
    UrunGetirUseCase,
    UrunOlusturUseCase,
    UrunGuncelleUseCase,
    UrunSilUseCase,
    KritikUrunleriGetirUseCase,
)
from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo


# ── Repository factory ──

def get_urun_repo(db: Session = Depends(get_db)):
    return SqlAlchemyUrunRepository(db)


# ── Use case factory'leri ──

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
