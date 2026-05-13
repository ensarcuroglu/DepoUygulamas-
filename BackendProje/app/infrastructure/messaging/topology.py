"""RabbitMQ exchange/queue/DLX idempotent topoloji declare.

Hem publisher hem consumer başlatılırken `declare(channel)` çağrılır; aynı
parametrelerle iki kez declare etmek RabbitMQ'da no-op'tur.

Topoloji:
  exchange       (topic, durable)
  ├── routing: lms.gorev_performans.*  →  queue
  dlx            (topic, durable)
  └── routing: <queue>.dlq             →  queue.dlq
  queue:         durable, x-dead-letter-exchange=dlx, x-dead-letter-routing-key=<queue>.dlq
  queue.dlq:     durable
"""

from __future__ import annotations

from dataclasses import dataclass


PERFORMANS_ROUTING_KEY_PREFIX = "lms.gorev_performans"


@dataclass(frozen=True)
class RabbitMqTopology:
    """Settings'ten beslenen topoloji parametreleri."""

    exchange: str
    queue: str
    dlx: str

    @property
    def dlq(self) -> str:
        return f"{self.queue}.dlq"

    @property
    def dlq_routing_key(self) -> str:
        return f"{self.queue}.dlq"

    def routing_key_for_event(self, event_tipi: str) -> str:
        return f"{PERFORMANS_ROUTING_KEY_PREFIX}.{event_tipi}"

    def routing_key_binding(self) -> str:
        return f"{PERFORMANS_ROUTING_KEY_PREFIX}.*"

    def declare(self, channel) -> None:
        """Exchange/queue/DLX'i idempotent olarak deklare eder."""
        # Dead-letter exchange + queue
        channel.exchange_declare(
            exchange=self.dlx, exchange_type="topic", durable=True
        )
        channel.queue_declare(queue=self.dlq, durable=True)
        channel.queue_bind(
            exchange=self.dlx, queue=self.dlq, routing_key=self.dlq_routing_key
        )

        # Ana exchange + queue (DLX bağlı)
        channel.exchange_declare(
            exchange=self.exchange, exchange_type="topic", durable=True
        )
        channel.queue_declare(
            queue=self.queue,
            durable=True,
            arguments={
                "x-dead-letter-exchange": self.dlx,
                "x-dead-letter-routing-key": self.dlq_routing_key,
            },
        )
        channel.queue_bind(
            exchange=self.exchange,
            queue=self.queue,
            routing_key=self.routing_key_binding(),
        )
