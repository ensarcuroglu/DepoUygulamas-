"""WebSocket connection manager + broadcast (snapshot/delta/event)."""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from fastapi import WebSocket

log = logging.getLogger(__name__)


class WsBroadcaster:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()

    def baglanti_sayisi(self) -> int:
        return len(self._connections)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        log.info("AGV WS client bagli (toplam=%d)", len(self._connections))

    def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        log.info("AGV WS client kopuk (toplam=%d)", len(self._connections))

    async def send_to(self, ws: WebSocket, payload: dict[str, Any]) -> None:
        await ws.send_text(json.dumps(payload, default=str))

    async def broadcast(self, payload: dict[str, Any]) -> None:
        if not self._connections:
            return
        text = json.dumps(payload, default=str)
        kopuk: list[WebSocket] = []
        for ws in list(self._connections):
            try:
                await ws.send_text(text)
            except Exception:
                kopuk.append(ws)
        for ws in kopuk:
            self.disconnect(ws)

    async def broadcast_delta(self, delta: dict[str, Any]) -> None:
        await self.broadcast({"tip": "delta", **delta})

    async def broadcast_event(self, event: dict[str, Any]) -> None:
        await self.broadcast({"tip": "event", **event})

    async def send_snapshot(self, ws: WebSocket, snapshot: dict[str, Any]) -> None:
        await self.send_to(ws, {"tip": "snapshot", **snapshot})


# ── Process-local singleton ──

_BROADCASTER: Optional[WsBroadcaster] = None


def set_broadcaster(b: WsBroadcaster) -> None:
    global _BROADCASTER
    _BROADCASTER = b


def get_broadcaster() -> WsBroadcaster:
    if _BROADCASTER is None:
        raise RuntimeError("WsBroadcaster henüz başlatılmadı")
    return _BROADCASTER


def reset_broadcaster_for_test() -> None:
    global _BROADCASTER
    _BROADCASTER = None
