"""DbOutbox Performans Event Publisher — Faz 1 implementasyonu.

Use case'lerden çağrılır; event'i doğrudan `gorev_performans_eventleri`
tablosuna `auto_commit=False` ile insert eder. Commit, çağıran use case'in
sahibi olduğu transaction tarafından atılır (transactional outbox).

APScheduler aggregator job daha sonra `aggregate_edildi=False` event'leri
okuyup `operator_vardiya_metrikleri` tablosuna upsert eder.

Faz 5'te aynı IPerformansEventPublisher arayüzünü implement eden bir
RabbitMQ adapter eklenebilir; use case kodu değişmez.
"""

from __future__ import annotations

from typing import Optional

from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    PerformansEventTipi,
    PerformansGorevTipi,
)
from app.core.repositories.operator_performans_repository import (
    IGorevPerformansEventRepository,
)
from app.core.services.performans_event_publisher import IPerformansEventPublisher


class DbOutboxPerformansEventPublisher(IPerformansEventPublisher):
    """DB outbox tabanlı publisher — Faz 1 default."""

    def __init__(self, event_repo: IGorevPerformansEventRepository) -> None:
        self._event_repo = event_repo

    def gorev_baslatildi(
        self,
        gorev_tipi: str,
        gorev_id: int,
        kullanici_id: int,
        depo_id: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None:
        self._yayinla(
            event_tipi=PerformansEventTipi.GOREV_BASLATILDI,
            gorev_tipi=gorev_tipi,
            gorev_id=gorev_id,
            kullanici_id=kullanici_id,
            depo_id=depo_id,
            payload=payload,
        )

    def gorev_tamamlandi(
        self,
        gorev_tipi: str,
        gorev_id: int,
        kullanici_id: int,
        sure_saniye: int,
        depo_id: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None:
        self._yayinla(
            event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
            gorev_tipi=gorev_tipi,
            gorev_id=gorev_id,
            kullanici_id=kullanici_id,
            depo_id=depo_id,
            sure_saniye=max(0, sure_saniye),
            payload=payload,
        )

    def gorev_iptal(
        self,
        gorev_tipi: str,
        gorev_id: int,
        kullanici_id: int,
        iptal_nedeni: Optional[str] = None,
        sure_saniye: Optional[int] = None,
        depo_id: Optional[int] = None,
        payload: Optional[dict] = None,
    ) -> None:
        self._yayinla(
            event_tipi=PerformansEventTipi.GOREV_IPTAL,
            gorev_tipi=gorev_tipi,
            gorev_id=gorev_id,
            kullanici_id=kullanici_id,
            depo_id=depo_id,
            sure_saniye=max(0, sure_saniye) if sure_saniye is not None else None,
            iptal_nedeni=iptal_nedeni,
            payload=payload,
        )

    def _yayinla(
        self,
        event_tipi: str,
        gorev_tipi: str,
        gorev_id: int,
        kullanici_id: int,
        depo_id: Optional[int] = None,
        sure_saniye: Optional[int] = None,
        iptal_nedeni: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> None:
        if not PerformansGorevTipi.gecerli_mi(gorev_tipi):
            raise ValueError(f"Geçersiz gorev_tipi: {gorev_tipi!r}")
        if not PerformansEventTipi.gecerli_mi(event_tipi):
            raise ValueError(f"Geçersiz event_tipi: {event_tipi!r}")
        if kullanici_id is None or kullanici_id <= 0:
            # Sahipsiz görev (örn. sistem iptali) — sessizce atla; KPI'ya yansımaz.
            return

        event = GorevPerformansEvent(
            event_tipi=event_tipi,
            gorev_tipi=gorev_tipi,
            gorev_id=gorev_id,
            kullanici_id=kullanici_id,
            depo_id=depo_id,
            sure_saniye=sure_saniye,
            iptal_nedeni=iptal_nedeni,
            payload=payload,
        )
        # auto_commit=False — outer use case transaction'ı commit'i taşır.
        self._event_repo.olustur(event, auto_commit=False)
