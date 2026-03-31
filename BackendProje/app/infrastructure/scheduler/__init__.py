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

logger = logging.getLogger(__name__)


class RaporScheduler:
    """APScheduler wrapper — zamanlı rapor tetikleyici."""

    def __init__(self) -> None:
        self._scheduler = None
        self._init_scheduler()

    def _init_scheduler(self) -> None:
        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger

            self._scheduler = BackgroundScheduler(timezone="Europe/Istanbul")
            self._scheduler.add_job(zamanlama_kontrol, CronTrigger(minute="*"))
        except ImportError:
            logger.warning("apscheduler kurulu değil — zamanlı raporlar devre dışı")

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
