"""DI — Kullanıcı, Destek Talebi, Sistem Log."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.core.auth import get_password_hash
from app.infrastructure.persistence.repositories import (
    SqlAlchemyDepoRepository,
    SqlAlchemyKullaniciRepository,
    SqlAlchemyDestekTalebiRepository,
    SqlAlchemySistemLogRepository,
)
from app.application.use_cases import (
    KullaniciListeleUseCase,
    KullaniciGetirUseCase,
    KullaniciGuncelleUseCase,
    KullaniciSilUseCase,
    DestekTalebiListeleUseCase,
    DestekTalebiGetirUseCase,
    DestekTalebiOlusturUseCase,
    DestekTalebiGuncelleUseCase,
    SistemLogListeleUseCase,
    SistemLogOlusturUseCase,
)


# ── Repository factory'leri ──

def get_kullanici_repo(db: Session = Depends(get_db)):
    return SqlAlchemyKullaniciRepository(db)


def get_kullanici_depo_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDepoRepository(db)


def get_destek_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDestekTalebiRepository(db)


def get_log_repo(db: Session = Depends(get_db)):
    return SqlAlchemySistemLogRepository(db)


# ── Kullanıcı use case factory'leri ──

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
    depo_repo=Depends(get_kullanici_depo_repo),
    log_repo=Depends(get_log_repo),
):
    return KullaniciGuncelleUseCase(
        kullanici_repo,
        depo_repo,
        log_repo,
        password_hasher=get_password_hash,
    )


def get_kullanici_sil_uc(
    kullanici_repo=Depends(get_kullanici_repo),
    log_repo=Depends(get_log_repo),
):
    return KullaniciSilUseCase(kullanici_repo, log_repo)


# ── Destek Talebi use case factory'leri ──

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


# ── Sistem Log use case factory'leri ──

def get_sistem_log_listele_uc(
    log_repo=Depends(get_log_repo),
):
    return SistemLogListeleUseCase(log_repo)


def get_sistem_log_olustur_uc(
    log_repo=Depends(get_log_repo),
):
    return SistemLogOlusturUseCase(log_repo)
