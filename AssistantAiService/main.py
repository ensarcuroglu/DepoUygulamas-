"""AssistantAiService FastAPI entrypoint.

Faz 2: LangGraph agent core. Lifespan'de ChatOllama + AsyncSqliteSaver acilir,
graph compile edilip `app.state.graph` uzerinden router'a iletilir. Test'lerde
`SQLITE_CHECKPOINT_PATH=:memory:` ile in-memory checkpointer kullanilir; ayrica
`get_graph` dependency override edilerek FakeChatModel ile baglanmis bir graph
enjekte edilebilir.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware.auth import InternalApiKeyMiddleware
from app.api.v1.routers import asistan_router, healthz_router
from app.application.agent.graph import build_graph
from app.core.config import get_settings
from app.infrastructure.checkpointer.sqlite import open_sqlite_checkpointer
from app.infrastructure.llm.ollama_factory import build_chat_model
from app.infrastructure.observability.langfuse_tracing import flush as flush_langfuse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("assistant-ai")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    settings = get_settings()
    log.info(
        "AssistantAiService hazir: ollama=%s model=%s backend=%s checkpointer=%s",
        settings.ollama_base_url,
        settings.assistant_llm_model,
        settings.backend_base_url,
        settings.sqlite_checkpoint_path,
    )
    llm = build_chat_model(settings)
    async with open_sqlite_checkpointer(settings.sqlite_checkpoint_path) as saver:
        graph = build_graph(llm, checkpointer=saver)
        app_.state.graph = graph
        log.info("LangGraph compiled with AsyncSqliteSaver")
        try:
            yield
        finally:
            flush_langfuse()
            log.info("AssistantAiService kapandi")


app = FastAPI(
    title="AssistantAiService",
    description="Kullanici/rol baglamli, Human-in-the-Loop depo asistani mikroservisi.",
    version="0.2.0",
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
app.include_router(asistan_router)
