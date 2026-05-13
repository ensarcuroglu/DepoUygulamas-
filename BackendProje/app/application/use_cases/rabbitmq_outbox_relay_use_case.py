"""RabbitMQ Outbox Relay Use Case.

`gorev_performans_eventleri` tablosundan `rabbitmq_yayinlandi=False`
event'leri batch halinde okur, RabbitMQ'ya publisher confirm ile yayınlar
ve sonuçları idempotent şekilde DB'ye yansıtır:
  * Confirm OK   → repo.yayinlandi_isaretle(event_id, now)
  * Hata         → repo.yayin_hatasi_kaydet(event_id, hata) (deneme +1)
  * Broker down  → batch'i kes, sonraki tetiklemede tekrar dener.

Yayını APScheduler job (`rabbitmq_outbox_relay_job`) periyodik çağırır.
Çağrı kendi DB session'ını alır; commit her event başına ayrı atılır
böylece broker confirm aldığımız her event kalıcı işaretlenir.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.core.repositories.operator_performans_repository import (
    IGorevPerformansEventRepository,
)
from app.infrastructure.messaging.connection import RabbitMqUnavailable
from app.infrastructure.messaging.publisher import RabbitMqPerformansPublisher


logger = logging.getLogger(__name__)


@dataclass
class OutboxRelaySonuc:
    okunan: int = 0
    yayinlanan: int = 0
    hatali: int = 0
    broker_kapali: bool = False


class RabbitMqOutboxRelayUseCase:
    """Outbox → RabbitMQ relay'i."""

    def __init__(
        self,
        event_repo: IGorevPerformansEventRepository,
        publisher: RabbitMqPerformansPublisher,
        batch_size: int = 100,
    ) -> None:
        self._event_repo = event_repo
        self._publisher = publisher
        self._batch_size = max(1, batch_size)

    def execute(self) -> OutboxRelaySonuc:
        sonuc = OutboxRelaySonuc()

        events = self._event_repo.yayinlanmamis_eventleri_getir(self._batch_size)
        sonuc.okunan = len(events)
        if not events:
            return sonuc

        try:
            self._publisher.open()
        except RabbitMqUnavailable as exc:
            logger.warning("RabbitMQ broker bağlantı hatası, batch atlanıyor: %s", exc)
            sonuc.broker_kapali = True
            return sonuc

        try:
            for event in events:
                if event.id is None:
                    # Outbox'tan dönen event'in id'si olmalı; defensive skip.
                    continue
                try:
                    self._publisher.publish(event)
                except RabbitMqUnavailable as exc:
                    logger.warning(
                        "RabbitMQ broker publish sırasında düştü, batch kesiliyor: %s",
                        exc,
                    )
                    sonuc.broker_kapali = True
                    self._event_repo.yayin_hatasi_kaydet(event.id, str(exc))
                    break
                except Exception as exc:  # noqa: BLE001 — broker/serializer hatalarını yakala
                    logger.error(
                        "Event %s yayınlanamadı: %s", event.event_uuid, exc
                    )
                    sonuc.hatali += 1
                    self._event_repo.yayin_hatasi_kaydet(event.id, str(exc))
                else:
                    self._event_repo.yayinlandi_isaretle(event.id)
                    sonuc.yayinlanan += 1
        finally:
            self._publisher.close()

        return sonuc
