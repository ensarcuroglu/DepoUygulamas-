"""
AgvSimService — Otonom Mobil Robot (AGV/AMR) simülasyon servisi.

Faz 0: Iskelet — sadece FastAPI boot + healthz + CORS.
Tick loop, robot state machine, pathfinding ve WS broadcaster Faz 1'de eklenecek.

Detaylı plan: /AGV_SIMULATION_PLAN.md
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Faz 1: tick loop burada başlatılacak (asyncio.create_task)
    yield


app = FastAPI(
    title="AGV Simülasyon Servisi",
    description="Depo içi AGV/AMR simülasyonu — WMS authoritative, AGV stateless-from-DB.",
    version="0.0.1",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["Sistem"])
def healthz():
    return {
        "status": "ok",
        "service": "AgvSimService",
        "version": app.version,
        "tick_hz": settings.TICK_HZ,
    }
