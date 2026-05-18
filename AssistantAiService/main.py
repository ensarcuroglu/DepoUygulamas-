"""AssistantAiService FastAPI entrypoint.

Faz 0: yalnizca iskelet — internal-api-key middleware + healthz endpoint.
Faz 2'de LangGraph agent ve chat router eklenecek.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.auth import InternalApiKeyMiddleware
from app.api.v1.routers import healthz_router
from app.core.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("assistant-ai")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    settings = get_settings()
    log.info(
        "AssistantAiService hazir: ollama=%s model=%s backend=%s",
        settings.ollama_base_url,
        settings.assistant_llm_model,
        settings.backend_base_url,
    )
    try:
        yield
    finally:
        log.info("AssistantAiService kapandi")


app = FastAPI(
    title="AssistantAiService",
    description="Kullanici/rol baglamli, Human-in-the-Loop depo asistani mikroservisi.",
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
