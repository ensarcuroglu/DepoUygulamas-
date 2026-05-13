"""RabbitMQ Operatör Performans Consumer.

`depo.lms.operator_metrikleri` queue'sundan mesaj tüketir, payload'daki
event_id ile DB'den `gorev_performans_eventleri` kaydını okur ve
`MetriklerAggregasyonUseCase.eventleri_isle` ile aggregasyonu çalıştırır.

Idempotency: DB'deki `aggregate_edildi=True` ise mesaj sadece ack'lenir.
Aynı event_id'nin iki kez ulaşması durumunda KPI sayaçları bozulmaz.

Hata davranışı:
  * Parse hatası / desteklenmeyen schema   → mesaj DLQ'ya nack
  * DB lookup başarısız (event yok)        → mesaj DLQ'ya nack
  * Aggregasyon DB hatası (transient)      → mesaj requeue (basic_nack requeue=True)
  * Bağlantı kopması                       → consumer loop yeniden bağlanır

Çalıştırma:
    python -m app.infrastructure.messaging.operator_performans_consumer

`RABBITMQ_ENABLED=false` ise süreç hiçbir queue'ya bağlanmadan beklemeden
çıkar (worker container'ı `restart: always` olsa da log ile bilgi verir).
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from pathlib import Path
from typing import Optional

# ml_models paketini sys.path'e ekle (sibling to BackendProje).
# `python -m app.infrastructure.messaging.operator_performans_consumer`
# çağrısında BackendProje cwd olmadığı için _ml_models_path otomatik
# tetiklenmez; root path elle eklenir.
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import pika  # noqa: E402
from pika.exceptions import AMQPConnectionError, AMQPError  # noqa: E402

from app.application.use_cases.operator_performans_use_cases import (  # noqa: E402
    MetriklerAggregasyonUseCase,
)
from app.core.config import Settings, get_settings  # noqa: E402
from app.core.services.operator_kpi_service import OperatorKpiService  # noqa: E402
from app.infrastructure.messaging.connection import (  # noqa: E402
    RabbitMqConnectionFactory,
    RabbitMqUnavailable,
)
from app.infrastructure.messaging.serializer import (  # noqa: E402
    deserialize_performans_event,
)
from app.infrastructure.messaging.topology import RabbitMqTopology  # noqa: E402
from app.infrastructure.persistence.repositories import (  # noqa: E402
    SqlAlchemyGorevPerformansEventRepository,
    SqlAlchemyOperatorVardiyaMetrikleriRepository,
)
from database import SessionLocal  # noqa: E402
from models import GorevPerformansEvent as GorevPerformansEventORM  # noqa: E402

logger = logging.getLogger(__name__)


_RECONNECT_DELAY_SEC = 5


class OperatorPerformansConsumer:
    """Queue tüketici — `start()` blocking, `stop()` graceful shutdown."""

    def __init__(
        self,
        connection_factory: RabbitMqConnectionFactory,
        topology: RabbitMqTopology,
        prefetch: int,
    ) -> None:
        self._factory = connection_factory
        self._topology = topology
        self._prefetch = prefetch
        self._connection: Optional[pika.BlockingConnection] = None
        self._channel = None
        self._stop_requested = False

    # ───────────────── lifecycle ─────────────────

    def start(self) -> None:
        """Blocking consume loop — bağlantı koparsa exp-backoff ile yeniden bağlanır."""
        logger.info("Operatör performans consumer başlatılıyor")
        while not self._stop_requested:
            try:
                self._connect_and_consume()
            except RabbitMqUnavailable as exc:
                logger.warning(
                    "RabbitMQ bağlanılamadı, %ds sonra tekrar: %s",
                    _RECONNECT_DELAY_SEC,
                    exc,
                )
                time.sleep(_RECONNECT_DELAY_SEC)
            except AMQPConnectionError as exc:
                logger.warning(
                    "RabbitMQ bağlantı koptu, %ds sonra tekrar: %s",
                    _RECONNECT_DELAY_SEC,
                    exc,
                )
                time.sleep(_RECONNECT_DELAY_SEC)
            except Exception as exc:  # noqa: BLE001 — son hat savunma
                logger.exception("Consumer beklenmeyen hata: %s", exc)
                time.sleep(_RECONNECT_DELAY_SEC)
        logger.info("Consumer durduruldu")

    def stop(self) -> None:
        self._stop_requested = True
        try:
            if self._channel is not None and self._channel.is_open:
                self._channel.stop_consuming()
        except Exception:  # noqa: BLE001 — best-effort
            pass

    # ───────────────── private ─────────────────

    def _connect_and_consume(self) -> None:
        self._connection = self._factory.connect()
        try:
            self._channel = self._connection.channel()
            self._topology.declare(self._channel)
            self._channel.basic_qos(prefetch_count=self._prefetch)
            self._channel.basic_consume(
                queue=self._topology.queue,
                on_message_callback=self._on_message,
                auto_ack=False,
            )
            logger.info(
                "Queue dinleniyor: queue=%s prefetch=%d",
                self._topology.queue,
                self._prefetch,
            )
            self._channel.start_consuming()
        finally:
            self._factory.safe_close(self._connection)
            self._connection = None
            self._channel = None

    def _on_message(self, channel, method, properties, body) -> None:  # noqa: ARG002
        delivery_tag = method.delivery_tag
        try:
            event = deserialize_performans_event(body)
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Mesaj parse edilemedi, DLQ'ya: %s body_preview=%s",
                exc,
                (body[:200] if isinstance(body, bytes) else str(body)[:200]),
            )
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
            return

        event_id = event.id
        if event_id is None:
            logger.error(
                "Mesajda event_id yok (uuid=%s), DLQ'ya", event.event_uuid
            )
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
            return

        try:
            islenen = _process_event_id(event_id)
        except Exception as exc:  # noqa: BLE001 — transient DB hatası → requeue
            logger.warning(
                "Event %s işlenirken hata, requeue: %s", event_id, exc
            )
            channel.basic_nack(delivery_tag=delivery_tag, requeue=True)
            return

        if islenen is None:
            # Event DB'de bulunamadı — payload'da var ama tabloda yok.
            # Sonsuz requeue olmasın diye DLQ'ya yönlendir.
            logger.error(
                "Event id=%s DB'de yok, DLQ'ya (uuid=%s)",
                event_id,
                event.event_uuid,
            )
            channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
            return

        channel.basic_ack(delivery_tag=delivery_tag)


# ─────────────────────── DB tarafı (per-message) ───────────────────────


def _process_event_id(event_id: int) -> Optional[bool]:
    """Tek event'i DB'den oku ve aggregate et — idempotent.

    Dönüş:
        None  → event DB'de bulunamadı
        True  → event işlendi (zaten aggregate ise no-op + True)
    """
    db = SessionLocal()
    try:
        orm = (
            db.query(GorevPerformansEventORM)
            .filter(GorevPerformansEventORM.id == event_id)
            .with_for_update()
            .first()
        )
        if orm is None:
            db.rollback()
            return None

        if orm.aggregate_edildi:
            db.rollback()
            return True

        event_repo = SqlAlchemyGorevPerformansEventRepository(db)
        metrik_repo = SqlAlchemyOperatorVardiyaMetrikleriRepository(db)
        uc = MetriklerAggregasyonUseCase(
            event_repo=event_repo,
            metrik_repo=metrik_repo,
            kpi_service=OperatorKpiService(),
        )

        # Mapper'ı kullanmak yerine elden geçer entity üretmek yerine repo
        # üzerinden tek event entity'sini elde etmek için doğrudan mapper
        # cağrısı yapıyoruz — refactor sırasında dökünmek istemedik.
        from app.infrastructure.persistence.mappers.operator_performans_mapper import (
            gorev_performans_event_to_entity,
        )

        entity = gorev_performans_event_to_entity(orm)
        uc.eventleri_isle([entity])
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ─────────────────────── entry point ───────────────────────


def _build_consumer(settings: Settings) -> OperatorPerformansConsumer:
    topology = RabbitMqTopology(
        exchange=settings.rabbitmq_exchange,
        queue=settings.rabbitmq_queue,
        dlx=settings.rabbitmq_dlx,
    )
    factory = RabbitMqConnectionFactory(url=settings.rabbitmq_url)
    return OperatorPerformansConsumer(
        connection_factory=factory,
        topology=topology,
        prefetch=settings.rabbitmq_prefetch,
    )


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    settings = get_settings()
    if not settings.rabbitmq_enabled:
        logger.warning(
            "RABBITMQ_ENABLED=false — consumer worker boş döngüde bekliyor "
            "(restart loop tetiklenmesin diye)."
        )
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            return 0

    consumer = _build_consumer(settings)

    def _signal_handler(signum, frame):  # noqa: ARG001
        logger.info("Sinyal alındı (%s), consumer durduruluyor", signum)
        consumer.stop()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    try:
        consumer.start()
    except AMQPError as exc:
        logger.error("AMQP fatal hata: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
