"""ExcelAiService FastAPI entrypoint."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.auth import InternalApiKeyMiddleware
from app.api.v1.routers import excel_router, healthz_router
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("excel-ai")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    settings = get_settings()
    log.info(
        "ExcelAiService hazir: wms=%s ollama=%s text_model=%s max_file_mb=%s max_rows=%s",
        settings.wms_base_url,
        settings.ollama_base_url,
        settings.ollama_text_model,
        settings.max_file_size_mb,
        settings.max_rows,
    )
    try:
        yield
    finally:
        log.info("ExcelAiService kapandi")


app = FastAPI(
    title="ExcelAiService",
    description="AI destekli Excel yorumlama ve WMS sema esleme mikroservisi.",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(InternalApiKeyMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(healthz_router)
app.include_router(excel_router)
