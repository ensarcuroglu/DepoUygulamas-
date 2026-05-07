"""Asyncio tick loop — her 1/TICK_HZ sn'de bir robotları ilerletir, WS yayını."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.application.use_cases.gorev_atama import GorevAtamaUseCase
from app.application.use_cases.tick import TickUseCase
from app.core.services.world import World
from app.infrastructure.ws_broadcaster import WsBroadcaster

log = logging.getLogger(__name__)


class TickLoop:
    def __init__(self, world: World, broadcaster: WsBroadcaster, hz: int) -> None:
        self.world = world
        self.broadcaster = broadcaster
        self.interval = 1.0 / max(1, hz)
        self._tick_uc = TickUseCase()
        self._atama_uc = GorevAtamaUseCase()
        self._task: Optional[asyncio.Task[None]] = None

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
            "AGV tick loop baslatildi (interval=%.3fs, hz~%.1f)",
            self.interval,
            1.0 / self.interval,
        )
        try:
            while True:
                await asyncio.sleep(self.interval)
                events, delta = await self._bir_tick()
                # WS yayını lock dışında — yavaş client tick'i bloke etmesin
                await self.broadcaster.broadcast_delta(delta)
                for ev in events:
                    await self.broadcaster.broadcast_event(ev)
        except asyncio.CancelledError:
            log.info("AGV tick loop iptal edildi")
            raise
        except Exception:
            log.exception("AGV tick loop crashed")
            raise

    async def _bir_tick(self) -> tuple[list[dict], dict]:
        async with self.world.lock:
            events = self._tick_uc.execute(self.world)
            events.extend(self._atama_uc.execute(self.world))
            delta = self.world.snapshot_delta()
        return events, delta
