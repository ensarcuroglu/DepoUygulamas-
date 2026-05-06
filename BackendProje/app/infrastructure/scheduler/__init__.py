"""
Scheduler paketi — public API.

Kullanım (main.py lifespan):
    scheduler = RaporScheduler()
    scheduler.start()
    ...
    scheduler.shutdown()
"""

import logging
from app.infrastructure.scheduler.rapor_scheduler import zamanlama_kontrol
from app.infrastructure.scheduler.staging_uyari_job import staging_uyari_kontrol
from app.infrastructure.scheduler.talep_tahmin_job import talep_tahmin_precompute
from app.infrastructure.scheduler.operator_metrik_aggregator_job import (
    operator_metrikleri_aggregate_et,
)

logger = logging.getLogger(__name__)


class RaporScheduler:
    """APScheduler wrapper — zamanlı rapor ve staging uyarı tetikleyici."""

    def __init__(self) -> None:
        self._scheduler = None
        self._init_scheduler()

    def _init_scheduler(self) -> None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger

            self._scheduler = BackgroundScheduler(timezone="Europe/Istanbul")
            # Zamanlı raporlar — her dakika
            self._scheduler.add_job(zamanlama_kontrol, CronTrigger(minute="*"))
            # Staging uyarısı — her gün sabah 07:00
            self._scheduler.add_job(
                staging_uyari_kontrol,
                CronTrigger(hour=7, minute=0),
                id="staging_uyari",
                replace_existing=True,
            )
            # Talep tahmini precompute — her gece 02:00 (satıncı sabah cache'ten okur)
            self._scheduler.add_job(
                talep_tahmin_precompute,
                CronTrigger(hour=2, minute=0),
                id="talep_tahmin_precompute",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
            # Operatör performans metrikleri aggregator — her 5 dakikada bir
            self._scheduler.add_job(
                operator_metrikleri_aggregate_et,
                CronTrigger(minute="*/5"),
                id="operator_metrikleri_aggregate",
                replace_existing=True,
                max_instances=1,
                coalesce=True,
            )
        except ImportError:
            logger.warning("apscheduler kurulu değil — zamanlı görevler devre dışı")

    @property
    def aktif(self) -> bool:
        return self._scheduler is not None

    def start(self) -> None:
        if self._scheduler:
            self._scheduler.start()
            logger.info("APScheduler başlatıldı")

    def shutdown(self) -> None:
        if self._scheduler:
            self._scheduler.shutdown()
            logger.info("APScheduler durduruldu")
