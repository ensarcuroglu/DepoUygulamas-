"""
AgvSimService — Otonom Mobil Robot (AGV/AMR) simülasyon servisi.

Faz 1: Tick loop + A* pathfinding + WS broadcaster + görev kabul endpoint.

Detaylı plan: /AGV_SIMULATION_PLAN.md
"""

from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path as FsPath

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routers import gorevler as gorevler_router
from app.api.v1.routers import robotlar as robotlar_router
from app.api.v1.routers import test_paneli as test_paneli_router
from app.api.v1.routers import ws as ws_router
from app.core.entities.grid import Cell
from app.core.entities.robot import Robot, RobotDurum, Yon
from app.core.services.wms_callback_port import (
    IWmsCallbackPort,
    NoOpWmsCallbackPort,
)
from app.core.services.world import World, set_world
from app.infrastructure.grid_loader import gridi_jsondan_yukle
from app.infrastructure.wms_client import HttpWmsCallbackPort
from app.infrastructure.ws_broadcaster import WsBroadcaster, set_broadcaster
from app.runtime.tick_loop import TickLoop
from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("agv")


def _robotlari_olustur(world: World, grid_path: str) -> None:
    """JSON'daki `_baslangic_robot_konumlari`'na göre robotları oluştur.

    Yoksa şarj konumlarına; o da yoksa (0,0) komşusu BOS bir hücreye düşer.
    """
    veri = json.loads(FsPath(grid_path).read_text(encoding="utf-8"))
    konumlar = veri.get("_baslangic_robot_konumlari") or []
    if not konumlar:
        # Default: ilk 2 sarj konumu, yoksa ilk gecilebilir hücre
        for i, c in enumerate(world.grid.sarj_konumlari[:2]):
            konumlar.append({"id": f"AGV-{i + 1:02d}", "x": c.x, "y": c.y})
        if not konumlar:
            konumlar.append({"id": "AGV-01", "x": 0, "y": world.grid.yukseklik - 1})

    for k in konumlar:
        x, y = int(k["x"]), int(k["y"])
        world.robot_ekle(
            Robot(
                id=str(k["id"]),
                x=x,
                y=y,
                durum=RobotDurum.BOS,
                yon=Yon.KUZEY,
                bekleme_konumu=Cell(x, y),
            )
        )
    log.info("AGV robotlari olusturuldu: %s", [r.id for r in world.robotlar.values()])


def _build_wms_callback() -> IWmsCallbackPort:
    """INTERNAL_API_KEY tanımlıysa HttpWmsCallbackPort, aksi halde NoOp."""
    if settings.INTERNAL_API_KEY:
        return HttpWmsCallbackPort(
            wms_base_url=settings.WMS_BASE_URL,
            api_key=settings.INTERNAL_API_KEY,
        )
    log.warning(
        "INTERNAL_API_KEY tanimli degil — WMS callback NoOp moduda (gorev WMS'te kapanmaz)"
    )
    return NoOpWmsCallbackPort()


@asynccontextmanager
async def lifespan(app_: FastAPI):
    grid = gridi_jsondan_yukle(settings.GRID_JSON_PATH)
    world = World(grid=grid)
    _robotlari_olustur(world, settings.GRID_JSON_PATH)
    set_world(world)

    broadcaster = WsBroadcaster()
    set_broadcaster(broadcaster)

    wms_callback = _build_wms_callback()
    tick = TickLoop(world, broadcaster, settings.TICK_HZ, wms_callback=wms_callback)
    tick.start()
    log.info(
        "AGV servisi hazir — grid=%dx%d, raf=%d, robot=%d, tick=%dHz, wms=%s",
        grid.genislik,
        grid.yukseklik,
        len(grid.raflar),
        len(world.robotlar),
        settings.TICK_HZ,
        type(wms_callback).__name__,
    )
    try:
        yield
    finally:
        await tick.stop()
        log.info("AGV servisi kapandi")


app = FastAPI(
    title="AGV Simülasyon Servisi",
    description="Depo içi AGV/AMR simülasyonu — WMS authoritative, AGV stateless-from-DB.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gorevler_router.router)
app.include_router(robotlar_router.router)
app.include_router(ws_router.router)
if settings.AGV_TEST_PANEL_ENABLED:
    app.include_router(test_paneli_router.router)
    log.info("AGV test paneli endpoint'leri etkin (/api/agv/test/*)")


@app.get("/healthz", tags=["Sistem"])
def healthz() -> dict:
    return {
        "status": "ok",
        "service": "AgvSimService",
        "version": app.version,
        "tick_hz": settings.TICK_HZ,
    }
