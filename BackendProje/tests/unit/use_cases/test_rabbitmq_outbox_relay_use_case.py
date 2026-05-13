"""Unit testleri — RabbitMqOutboxRelayUseCase.

Mock publisher ve fake repository ile relay davranışı doğrulanır:
  * Tüm event'ler başarıyla yayınlanırsa hepsi mark_published olur.
  * Bir event publish() exception atarsa yayın_hatası kaydı atılır,
    sonraki event'ler etkilenmez.
  * Broker açılışta RabbitMqUnavailable fırlatırsa batch atlanır,
    DB değişmez.
  * Publish sırasında RabbitMqUnavailable çıkarsa batch kesilir,
    hatadan sonraki event'ler dokunulmaz kalır.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import pytest

from app.application.use_cases.rabbitmq_outbox_relay_use_case import (
    RabbitMqOutboxRelayUseCase,
)
from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    PerformansEventTipi,
    PerformansGorevTipi,
)
from app.infrastructure.messaging.connection import RabbitMqUnavailable


pytestmark = pytest.mark.unit


# ─────────────────────────── helpers ───────────────────────────


@dataclass
class _FakeRepo:
    eventler: List[GorevPerformansEvent]
    yayinlananlar: List[int] = field(default_factory=list)
    hatalar: List[tuple[int, str]] = field(default_factory=list)

    def yayinlanmamis_eventleri_getir(self, limit: int = 100):
        return list(self.eventler[:limit])

    def yayinlandi_isaretle(
        self,
        event_id: int,
        yayin_tarihi: Optional[datetime] = None,
        auto_commit: bool = True,
    ) -> bool:
        self.yayinlananlar.append(event_id)
        return True

    def yayin_hatasi_kaydet(
        self, event_id: int, hata: str, auto_commit: bool = True
    ) -> bool:
        self.hatalar.append((event_id, hata))
        return True


class _FakePublisher:
    """Hata `publish_exc_at`'da bir kez atılır; sonra normal davranır."""

    def __init__(
        self,
        open_exc: Optional[Exception] = None,
        publish_exc_at: Optional[int] = None,
        publish_exc: Optional[Exception] = None,
    ) -> None:
        self._open_exc = open_exc
        self._publish_exc_at = publish_exc_at
        self._publish_exc = publish_exc
        self.opened = False
        self.closed = False
        self.publish_attempt = 0
        self.published: List[str] = []

    def open(self) -> None:
        if self._open_exc:
            raise self._open_exc
        self.opened = True

    def publish(self, event: GorevPerformansEvent) -> None:
        attempt_idx = self.publish_attempt
        self.publish_attempt += 1
        if (
            self._publish_exc is not None
            and self._publish_exc_at is not None
            and attempt_idx == self._publish_exc_at
        ):
            raise self._publish_exc
        self.published.append(event.event_uuid or "")

    def close(self) -> None:
        self.closed = True


def _ornek_event(idx: int) -> GorevPerformansEvent:
    return GorevPerformansEvent(
        id=idx,
        event_uuid=f"uuid-{idx}",
        event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
        gorev_tipi=PerformansGorevTipi.YERLESTIRME,
        gorev_id=1000 + idx,
        kullanici_id=10,
        depo_id=1,
        sure_saniye=300,
        olusturma_tarihi=datetime(2026, 5, 13, 12, 0, 0),
    )


# ─────────────────────────── tests ───────────────────────────


class TestRabbitMqOutboxRelay:
    def test_bos_outbox_no_op(self):
        repo = _FakeRepo(eventler=[])
        publisher = _FakePublisher()
        uc = RabbitMqOutboxRelayUseCase(repo, publisher, batch_size=10)

        sonuc = uc.execute()

        assert sonuc.okunan == 0
        assert sonuc.yayinlanan == 0
        assert sonuc.broker_kapali is False
        assert publisher.opened is False  # boş batch için broker'a dokunma

    def test_hepsi_basarili_yayinlanir(self):
        events = [_ornek_event(i) for i in range(1, 4)]
        repo = _FakeRepo(eventler=events)
        publisher = _FakePublisher()
        uc = RabbitMqOutboxRelayUseCase(repo, publisher, batch_size=10)

        sonuc = uc.execute()

        assert sonuc.okunan == 3
        assert sonuc.yayinlanan == 3
        assert sonuc.hatali == 0
        assert repo.yayinlananlar == [1, 2, 3]
        assert publisher.closed is True

    def test_publish_hatasi_deneme_sayisi_artirir(self):
        events = [_ornek_event(i) for i in range(1, 4)]
        repo = _FakeRepo(eventler=events)
        publisher = _FakePublisher(
            publish_exc_at=1,
            publish_exc=RuntimeError("serializer bug"),
        )
        uc = RabbitMqOutboxRelayUseCase(repo, publisher, batch_size=10)

        sonuc = uc.execute()

        # event 1 yayınlandı, event 2 hata, event 3 yayınlandı (batch devam)
        assert sonuc.yayinlanan == 2
        assert sonuc.hatali == 1
        assert repo.yayinlananlar == [1, 3]
        assert len(repo.hatalar) == 1
        assert repo.hatalar[0][0] == 2
        assert "serializer bug" in repo.hatalar[0][1]

    def test_broker_acilista_kapali_ise_batch_atlanir(self):
        events = [_ornek_event(i) for i in range(1, 3)]
        repo = _FakeRepo(eventler=events)
        publisher = _FakePublisher(open_exc=RabbitMqUnavailable("connection refused"))
        uc = RabbitMqOutboxRelayUseCase(repo, publisher, batch_size=10)

        sonuc = uc.execute()

        assert sonuc.okunan == 2
        assert sonuc.yayinlanan == 0
        assert sonuc.broker_kapali is True
        assert repo.yayinlananlar == []
        assert repo.hatalar == []

    def test_publish_sirasinda_broker_dususe_batch_kesilir(self):
        events = [_ornek_event(i) for i in range(1, 4)]
        repo = _FakeRepo(eventler=events)
        publisher = _FakePublisher(
            publish_exc_at=1,
            publish_exc=RabbitMqUnavailable("connection lost"),
        )
        uc = RabbitMqOutboxRelayUseCase(repo, publisher, batch_size=10)

        sonuc = uc.execute()

        # event 1 yayınlandı, event 2 broker düştü → hata kaydedildi, batch kesildi
        assert sonuc.yayinlanan == 1
        assert sonuc.broker_kapali is True
        assert repo.yayinlananlar == [1]
        assert len(repo.hatalar) == 1
        assert repo.hatalar[0][0] == 2

    def test_batch_size_limit_uygulanir(self):
        events = [_ornek_event(i) for i in range(1, 6)]
        repo = _FakeRepo(eventler=events)
        publisher = _FakePublisher()
        uc = RabbitMqOutboxRelayUseCase(repo, publisher, batch_size=2)

        sonuc = uc.execute()

        assert sonuc.okunan == 2
        assert sonuc.yayinlanan == 2
