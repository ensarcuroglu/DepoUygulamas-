"""DataGenService FastAPI entrypoint.

Sentetik depo verisi üretici servisi. Detay: DOCS/DATA_GEN_SERVICE_ENTEGRASYON_PLANI.md
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import healthz_router, scenarios_router
from app.core.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("data-gen")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    settings = get_settings()
    log.info(
        "DataGenService hazir: backend=%s rabbit=%s seed=%s locale=%s batch=%s conc=%s",
        settings.backend_base_url,
        settings.rabbitmq_url,
        settings.default_seed,
        settings.locale,
        settings.batch_size,
        settings.concurrency,
    )
    try:
        yield
    finally:
        log.info("DataGenService kapandi")


app = FastAPI(
    title="DataGenService",
    description="Sentetik WMS veri üretici mikroservisi.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(healthz_router)
app.include_router(scenarios_router)
