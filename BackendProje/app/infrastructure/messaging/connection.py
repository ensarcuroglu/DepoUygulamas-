"""RabbitMQ BlockingConnection factory.

Sync pika ile uyumlu basit factory. Bağlantı broker kapalıyken yapılıyorsa
`RabbitMqUnavailable` fırlatır — çağıran (relay job) bunu yakalayıp deneme
sayacını arttırır.
"""

from __future__ import annotations

import logging
from typing import Optional

import pika
from pika.exceptions import AMQPConnectionError

logger = logging.getLogger(__name__)


class RabbitMqUnavailable(RuntimeError):
    """Broker'a bağlanılamadığında fırlatılır."""


class RabbitMqConnectionFactory:
    """Verilen URL üzerinden BlockingConnection üretir.

    Bağlantılar her publish iteration'ında yeniden açılmaz; relay job
    bir bağlantı açar, batch boyunca kullanır, sonra kapatır.
    """

    def __init__(
        self,
        url: str,
        connection_attempts: int = 1,
        socket_timeout: float = 5.0,
        heartbeat: int = 30,
    ) -> None:
        self._url = url
        self._connection_attempts = connection_attempts
        self._socket_timeout = socket_timeout
        self._heartbeat = heartbeat

    def connect(self) -> pika.BlockingConnection:
        try:
            params = pika.URLParameters(self._url)
            params.connection_attempts = self._connection_attempts
            params.socket_timeout = self._socket_timeout
            params.heartbeat = self._heartbeat
            return pika.BlockingConnection(params)
        except AMQPConnectionError as exc:
            raise RabbitMqUnavailable(f"RabbitMQ broker bağlantı hatası: {exc}") from exc

    def safe_close(self, connection: Optional[pika.BlockingConnection]) -> None:
        if connection is None:
            return
        try:
            if connection.is_open:
                connection.close()
        except Exception as exc:  # noqa: BLE001 — close best-effort
            logger.warning("RabbitMQ bağlantı kapatma uyarısı: %s", exc)
