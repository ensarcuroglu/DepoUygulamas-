"""DI — Rapor (Şablon, Log, Schedule, Veri), Dashboard."""

from fastapi import Depends
from sqlalchemy.orm import Session

from database import get_db
from app.infrastructure.persistence.repositories import (
    SqlAlchemyRaporSablonuRepository,
    SqlAlchemyRaporLoguRepository,
    SqlAlchemyRaporScheduleRepository,
    SqlAlchemyRaporVeriRepository,
    SqlAlchemyDashboardRepository,
)
from app.application.use_cases import (
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
)
from app.application.use_cases.dashboard_use_cases import DashboardIstatistikGetirUseCase
from app.infrastructure.di.modules.kullanici_destek_di import get_log_repo


# ── Repository factory'leri ──

def get_rapor_sablon_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporSablonuRepository(db)


def get_rapor_log_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporLoguRepository(db)


def get_rapor_schedule_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporScheduleRepository(db)


def get_rapor_veri_repo(db: Session = Depends(get_db)):
    return SqlAlchemyRaporVeriRepository(db)


def get_dashboard_repo(db: Session = Depends(get_db)):
    return SqlAlchemyDashboardRepository(db)


# ── Rapor Şablonu use case factory'leri ──

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


# ── Rapor Logu use case factory'leri ──

def get_rapor_logu_listele_uc(
    rapor_log_repo=Depends(get_rapor_log_repo),
):
    return RaporLoguListeleUseCase(rapor_log_repo)


def get_rapor_logu_yaz_uc(
    rapor_log_repo=Depends(get_rapor_log_repo),
):
    return RaporLoguYazUseCase(rapor_log_repo)


# ── Rapor Schedule use case factory'leri ──

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


# ── Rapor Veri + Export use case factory'leri ──

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


# ── Dashboard use case factory'leri ──

def get_dashboard_istatistik_uc(
    dashboard_repo=Depends(get_dashboard_repo),
):
    return DashboardIstatistikGetirUseCase(dashboard_repo)
