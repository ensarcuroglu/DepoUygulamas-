"""WS /ws/agv — canlı telemetri yayını."""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.services.world import get_world
from app.infrastructure.ws_broadcaster import get_broadcaster

log = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/agv")
async def agv_ws(ws: WebSocket) -> None:
    broadcaster = get_broadcaster()
    world = get_world()

    await broadcaster.connect(ws)
    try:
        async with world.lock:
            snapshot = world.snapshot_tam()
        await broadcaster.send_snapshot(ws, snapshot)

        # Faz 1: client → server mesajı yok. Bağlantıyı açık tut.
        # Disconnect olunca WebSocketDisconnect raise edilir.
        while True:
            try:
                await ws.receive_text()
            except WebSocketDisconnect:
                raise
            except Exception:
                # Client binary/ping gönderirse görmezden gel
                await asyncio.sleep(0)
    except WebSocketDisconnect:
        log.debug("AGV WS client kopuk")
    finally:
        broadcaster.disconnect(ws)
