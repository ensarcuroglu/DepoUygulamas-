"""DI — Sipariş, İrsaliye, Sevkiyat Planı, Mal Kabul İrsaliyesi, Stok Çıkış Service."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import (
    SqlAlchemySiparisRepository,
    SqlAlchemyIrsaliyeRepository,
    SqlAlchemySevkiyatPlaniRepository,
)
from app.application.use_cases import (
    SiparisListeleUseCase,
    SiparisGetirUseCase,
    SiparisOlusturUseCase,
    SiparisGuncelleUseCase,
    SiparisSilUseCase,
    IrsaliyeListeleUseCase,
    IrsaliyeGetirUseCase,
    IrsaliyeOlusturUseCase,
    IrsaliyeGuncelleUseCase,
    IrsaliyeYazdirVerisiGetirUseCase,
    SevkiyatPlaniListeleUseCase,
    SevkiyatPlaniGetirUseCase,
    SevkiyatPlaniOlusturUseCase,
    SevkiyatPlaniGuncelleUseCase,
    SevkiyatPlaniSilUseCase,
    MalKabulIrsaliyeListeleUseCase,
    MalKabulIrsaliyeGetirUseCase,
    MalKabulIrsaliyeOlusturUseCase,
    MalKabulIrsaliyeGuncelleUseCase,
    MalKabulIrsaliyeSilUseCase,
)
from app.core.services.stok_cikis_domain_service import StokCikisDomainService

from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo
from app.infrastructure.di.modules.urun_di import get_urun_repo
from app.infrastructure.di.modules.katalog_di import get_tedarikci_repo
from app.infrastructure.di.modules.depo_envanter_di import (
    get_depo_repo,
    get_raf_repo,
    get_lot_repo,
    get_palet_repo,
    get_hareket_repo,
    get_mal_kabul_irsaliye_repo,
)


# ── Repository factory'leri ──

def get_siparis_repo(db: Session = Depends(get_db)):
    return SqlAlchemySiparisRepository(db)


def get_irsaliye_repo(db: Session = Depends(get_db)):
    return SqlAlchemyIrsaliyeRepository(db)


def get_sevkiyat_repo(db: Session = Depends(get_db)):
    return SqlAlchemySevkiyatPlaniRepository(db)


# ── Stok Çıkış Domain Service factory ──

def get_stok_cikis_service(
    palet_repo=Depends(get_palet_repo),
    hareket_repo=Depends(get_hareket_repo),
    log_repo=Depends(get_log_repo),
):
    return StokCikisDomainService(palet_repo, hareket_repo, log_repo)


# ── Sipariş use case factory'leri ──

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


# ── İrsaliye use case factory'leri ──

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


# ── Sevkiyat Planı use case factory'leri ──

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


# ── Mal Kabul İrsaliyesi use case factory'leri ──

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
