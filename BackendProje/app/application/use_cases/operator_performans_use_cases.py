"""Operatör Performans Use Case'leri (LMS — Faz 1).

Faz 1 kapsamı veri toplama; sorgu/raporlama use case'leri Faz 2'de
gelir. Burada tek use case var:

    MetriklerAggregasyonUseCase
      - APScheduler job tarafından periyodik çağrılır.
      - Bekleyen `gorev_performans_eventleri` kayıtlarını okur,
        OperatorKpiService ile vardiya kovalarına böler,
        operator_vardiya_metrikleri tablosuna upsert eder ve
        işlenen event'leri `aggregate_edildi=True` işaretler.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.repositories.operator_performans_repository import (
    IGorevPerformansEventRepository,
    IOperatorVardiyaMetrikleriRepository,
)
from app.core.services.operator_kpi_service import OperatorKpiService

logger = logging.getLogger(__name__)


@dataclass
class AggregasyonSonucDTO:
    islenen_event: int
    guncellenen_vardiya: int
    bekleyen_kalan: int


class MetriklerAggregasyonUseCase:
    """Outbox event'leri tüketip vardiya metriklerini günceller."""

    def __init__(
        self,
        event_repo: IGorevPerformansEventRepository,
        metrik_repo: IOperatorVardiyaMetrikleriRepository,
        kpi_service: OperatorKpiService,
        batch_limit: int = 500,
    ) -> None:
        self._event_repo = event_repo
        self._metrik_repo = metrik_repo
        self._kpi = kpi_service
        self._batch_limit = batch_limit

    def execute(self) -> AggregasyonSonucDTO:
        eventler = self._event_repo.bekleyen_eventleri_getir(limit=self._batch_limit)
        if not eventler:
            return AggregasyonSonucDTO(
                islenen_event=0, guncellenen_vardiya=0, bekleyen_kalan=0
            )

        deltalar = self._kpi.vardiya_delta_uret(eventler)
        islenen_event_idleri: list[int] = []
        guncellenen = 0

        for anahtar, delta in deltalar:
            self._metrik_repo.upsert_artir(
                kullanici_id=anahtar.kullanici_id,
                vardiya_tarihi=anahtar.vardiya_tarihi,
                depo_id=delta.depo_id,
                yerlestirme_delta=delta.yerlestirme_delta,
                toplama_delta=delta.toplama_delta,
                iptal_delta=delta.iptal_delta,
                sure_saniye_delta=delta.sure_saniye_delta,
                auto_commit=True,
            )
            islenen_event_idleri.extend(delta.isleneN_event_idleri)
            guncellenen += 1

        if islenen_event_idleri:
            self._event_repo.aggregate_edildi_isaretle(
                islenen_event_idleri, auto_commit=True
            )

        bekleyen_kalan = max(0, len(eventler) - len(islenen_event_idleri))
        logger.info(
            "Performans aggregasyon: islenen=%d, vardiya_guncellendi=%d, kalan~%d",
            len(islenen_event_idleri),
            guncellenen,
            bekleyen_kalan,
        )
        return AggregasyonSonucDTO(
            islenen_event=len(islenen_event_idleri),
            guncellenen_vardiya=guncellenen,
            bekleyen_kalan=bekleyen_kalan,
        )
