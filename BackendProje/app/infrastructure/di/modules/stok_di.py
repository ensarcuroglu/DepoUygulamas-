"""DI — Stok Hareketi, Stok Sayım."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import SqlAlchemyStokSayimRepository
from app.application.use_cases import (
    StokHareketiListeleUseCase,
    StokHareketiOlusturUseCase,
    StokSayimListeleUseCase,
    StokSayimGetirUseCase,
    StokSayimBaslatUseCase,
    StokSayimKalemKaydetUseCase,
    StokSayimVaryansHesaplaUseCase,
    StokSayimOnaylaUseCase,
)
from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.urun_di import get_urun_repo
from app.infrastructure.di.modules.depo_envanter_di import (
    get_hareket_repo,
    get_lot_repo,
    get_palet_repo,
)


# ── Repository factory ──

def get_stok_sayim_repo(db: Session = Depends(get_db)):
    return SqlAlchemyStokSayimRepository(db)


# ── Stok Hareketi use case factory'leri ──

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


# ── Stok Sayım use case factory'leri ──

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
