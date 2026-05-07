"""Asyncio tick loop — her 1/TICK_HZ sn'de bir robotları ilerletir, WS yayını,
WMS callback dispatch'i."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Optional

from app.application.use_cases.gorev_atama import GorevAtamaUseCase
from app.application.use_cases.tick import TickUseCase
from app.core.services.world import World
from app.core.services.wms_callback_port import (
    IWmsCallbackPort,
    NoOpWmsCallbackPort,
    WmsCallbackPayload,
)
from app.infrastructure.ws_broadcaster import WsBroadcaster

log = logging.getLogger(__name__)


class TickLoop:
    def __init__(
        self,
        world: World,
        broadcaster: WsBroadcaster,
        hz: int,
        wms_callback: Optional[IWmsCallbackPort] = None,
    ) -> None:
        self.world = world
        self.broadcaster = broadcaster
        self.interval = 1.0 / max(1, hz)
        self._tick_uc = TickUseCase()
        self._atama_uc = GorevAtamaUseCase()
        self._wms_callback = wms_callback or NoOpWmsCallbackPort()
        self._task: Optional[asyncio.Task[None]] = None
        # In-flight callback'leri takip ederek aynı görev için duplicate
        # callback fire'ını engeller.
        self._in_flight: set[int] = set()

    def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._task = asyncio.create_task(self._run(), name="agv_tick_loop")

    async def stop(self) -> None:
        if self._task is None:
            return
        if not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def _run(self) -> None:
        log.info(
            "AGV tick loop baslatildi (interval=%.3fs, hz~%.1f, wms_callback=%s)",
            self.interval,
            1.0 / self.interval,
            type(self._wms_callback).__name__,
        )
        try:
            while True:
                await asyncio.sleep(self.interval)
                events, delta = await self._bir_tick()
                # WS yayını lock dışında — yavaş client tick'i bloke etmesin
                await self.broadcaster.broadcast_delta(delta)
                for ev in events:
                    await self.broadcaster.broadcast_event(ev)
                    if ev.get("olay") == "gorev_tamamlandi":
                        self._gorev_tamamlandi_callback_fire(ev)
        except asyncio.CancelledError:
            log.info("AGV tick loop iptal edildi")
            raise
        except Exception:
            log.exception("AGV tick loop crashed")
            raise

    async def _bir_tick(self) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        async with self.world.lock:
            events = self._tick_uc.execute(self.world)
            events.extend(self._atama_uc.execute(self.world))
            delta = self.world.snapshot_delta()
        return events, delta

    def _gorev_tamamlandi_callback_fire(self, event: dict[str, Any]) -> None:
        """Async WMS callback'i background task olarak başlat."""
        wms_gorev_id = event.get("wms_gorev_id")
        if wms_gorev_id is None:
            return
        if wms_gorev_id in self._in_flight:
            log.debug("WMS callback zaten in-flight gorev=%s, atlandi", wms_gorev_id)
            return
        self._in_flight.add(wms_gorev_id)
        asyncio.create_task(self._wms_callback_yap(event))

    async def _wms_callback_yap(self, event: dict[str, Any]) -> None:
        wms_gorev_id = event.get("wms_gorev_id")
        try:
            payload = WmsCallbackPayload(
                wms_gorev_id=wms_gorev_id,
                wms_gorev_tipi=event.get("wms_gorev_tipi", "Yerlestirme"),
                robot_id=event.get("robot_id", ""),
                gerceklesen_raf_id=event.get("gerceklesen_raf_id"),
                sim_baslama_tick=event.get("sim_baslama_tick"),
                sim_tamamlanma_tick=event.get("sim_tamamlanma_tick"),
            )
            ok = await self._wms_callback.gorev_tamamlandi(payload)
            if not ok:
                log.warning(
                    "WMS callback basarisiz gorev=%s — gorev WMS'te orphan kalabilir",
                    wms_gorev_id,
                )
        finally:
            self._in_flight.discard(wms_gorev_id)
