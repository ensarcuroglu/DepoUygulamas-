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
from datetime import date, timedelta
from typing import List, Optional

from app.application.dto.operator_performans_dto import (
    KendiPerformansOzetDTO,
    LeaderboardItemDTO,
    LeaderboardResponseDTO,
    OperatorMetrikItemDTO,
    OperatorOzetListResponseDTO,
)
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


class OperatorPerformansSorguUseCase:
    """KPI okuma uçları — özet, kullanıcı detay, leaderboard, /me."""

    def __init__(self, metrik_repo: IOperatorVardiyaMetrikleriRepository) -> None:
        self._metrik_repo = metrik_repo

    def ozet_getir(
        self,
        baslangic: Optional[date] = None,
        bitis: Optional[date] = None,
        depo_id: Optional[int] = None,
        kullanici_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 200,
    ) -> OperatorOzetListResponseDTO:
        kayitlar = self._metrik_repo.getir_aralik(
            kullanici_id=kullanici_id,
            depo_id=depo_id,
            baslangic=baslangic,
            bitis=bitis,
            skip=skip,
            limit=limit,
        )
        items = [OperatorMetrikItemDTO.from_entity(m) for m in kayitlar]
        return OperatorOzetListResponseDTO(items=items, toplam=len(items))

    def kullanici_detay_getir(
        self,
        kullanici_id: int,
        baslangic: Optional[date] = None,
        bitis: Optional[date] = None,
        limit: int = 90,
    ) -> List[OperatorMetrikItemDTO]:
        kayitlar = self._metrik_repo.getir_aralik(
            kullanici_id=kullanici_id,
            baslangic=baslangic,
            bitis=bitis,
            skip=0,
            limit=limit,
        )
        return [OperatorMetrikItemDTO.from_entity(m) for m in kayitlar]

    def leaderboard_getir(
        self,
        vardiya_tarihi: Optional[date] = None,
        depo_id: Optional[int] = None,
        limit: int = 10,
    ) -> LeaderboardResponseDTO:
        gun = vardiya_tarihi or date.today()
        kayitlar = self._metrik_repo.leaderboard_getir(
            vardiya_tarihi=gun, depo_id=depo_id, limit=limit
        )
        # UPH'a göre azalan sıralama (entity property'si üzerinden)
        kayitlar.sort(key=lambda m: (m.uph, m.toplam_gorev), reverse=True)
        items: list[LeaderboardItemDTO] = []
        for sira, m in enumerate(kayitlar[:limit], start=1):
            items.append(
                LeaderboardItemDTO(
                    sira=sira,
                    kullanici_id=m.kullanici_id,
                    operator_adi=m.operator_adi,
                    depo_id=m.depo_id,
                    depo_adi=m.depo_adi,
                    toplam_gorev=m.toplam_gorev,
                    toplam_aktif_saniye=m.toplam_aktif_saniye,
                    uph=m.uph,
                    hata_orani=m.hata_orani,
                )
            )
        return LeaderboardResponseDTO(vardiya_tarihi=gun, items=items)

    def kendi_metriklerim(
        self, kullanici_id: int, gun_sayisi: int = 7
    ) -> KendiPerformansOzetDTO:
        bugun = date.today()
        baslangic = bugun - timedelta(days=max(0, gun_sayisi - 1))
        kayitlar = self._metrik_repo.getir_aralik(
            kullanici_id=kullanici_id,
            baslangic=baslangic,
            bitis=bugun,
            skip=0,
            limit=gun_sayisi,
        )
        items = [OperatorMetrikItemDTO.from_entity(m) for m in kayitlar]
        bugun_kaydi = next(
            (i for i in items if i.vardiya_tarihi == bugun), None
        )
        return KendiPerformansOzetDTO(bugun=bugun_kaydi, son_gunler=items)
