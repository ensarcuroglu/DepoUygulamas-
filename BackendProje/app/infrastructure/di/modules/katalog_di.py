"""DI — Marka, Kategori, Tedarikçi."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import (
    SqlAlchemyMarkaRepository,
    SqlAlchemyKategoriRepository,
    SqlAlchemyTedarikciRepository,
)
from app.application.use_cases import (
    MarkaListeleUseCase,
    MarkaGetirUseCase,
    MarkaOlusturUseCase,
    MarkaGuncelleUseCase,
    MarkaSilUseCase,
    KategoriListeleUseCase,
    KategoriGetirUseCase,
    KategoriOlusturUseCase,
    KategoriGuncelleUseCase,
    KategoriSilUseCase,
    TedarikciListeleUseCase,
    TedarikciGetirUseCase,
    TedarikciOlusturUseCase,
    TedarikciGuncelleUseCase,
    TedarikciSilUseCase,
)
from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo


# ── Repository factory'leri ──

def get_marka_repo(db: Session = Depends(get_db)):
    return SqlAlchemyMarkaRepository(db)


def get_kategori_repo(db: Session = Depends(get_db)):
    return SqlAlchemyKategoriRepository(db)


def get_tedarikci_repo(db: Session = Depends(get_db)):
    return SqlAlchemyTedarikciRepository(db)


# ── Marka use case factory'leri ──

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


# ── Kategori use case factory'leri ──

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


# ── Tedarikçi use case factory'leri ──

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
