"""
WMS AI Sorgu Servisi — FastAPI giriş noktası.

Geliştirmeler (eski tek-dosyalı versiyona göre):
- LangChain LCEL pipeline (chains.py)
- Few-shot Türkçe örnekleri ile zengin sistem promptu (prompts.py)
- SQL guard: SELECT-only, yasaklı keyword/yorum, whitelist (sql_guard.py)
- Self-correction loop: SQL hatası → LLM'e hatayı geri verip düzelttirme
- SQL → doğal dil cevap üretimi (ikinci LLM çağrısı)
- Konuşma hafızası ile takip soruları (memory.py, session_id bazlı)
- ChatOllama (langchain-ollama) ile modern API kullanımı
- Konfigürasyon env'den: OLLAMA_MODEL, OLLAMA_BASE_URL, MAX_CORRECTION_ATTEMPTS, ...
"""

from __future__ import annotations

import logging
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()

# Pipeline import .env yüklendikten sonra olmalı (DB URI ve OLLAMA_* okunuyor)
from chat_orchestrator import get_chat_orchestrator  # noqa: E402
from chains import get_pipeline  # noqa: E402
from memory import Turn, store  # noqa: E402
from prompts import SCHEMA_DESCRIPTION  # noqa: E402
from route_examples import ROUTE_DOCS  # noqa: E402
from slash_commands import SlashCommandError  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("wms-ai")

app = FastAPI(title="WMS AI Sorgu Servisi", version="2.0")


# ----------------------------------------------------------------------------
# Şemalar
# ----------------------------------------------------------------------------

class SorguIstegi(BaseModel):
    soru: str = Field(..., min_length=2, max_length=500)
    session_id: str | None = Field(default=None, description="Takip soruları için oturum kimliği")
    debug: bool = Field(default=False, description="Üretilen SQL ve düzeltme logunu döndür")
    verbose: bool = Field(
        default=False,
        description="Çok-satır LIST için LLM cevabını dene (validation'dan geçemezse template fallback)",
    )


class SorguYaniti(BaseModel):
    soru: str
    cevap: str
    uretilen_sql: str
    session_id: str
    deneme_sayisi: int
    debug: dict | None = None


class ChatYaniti(BaseModel):
    soru: str
    cevap: str
    uretilen_sql: str | None
    session_id: str
    deneme_sayisi: int
    route: str
    route_source: str
    confidence: float | None = None
    sources: list[dict] = Field(default_factory=list)
    debug: dict | None = None


class OturumIstegi(BaseModel):
    session_id: str


# ----------------------------------------------------------------------------
# Endpoint'ler
# ----------------------------------------------------------------------------

@app.post("/api/ai/sorgula", response_model=SorguYaniti)
def ai_sorgula(istek: SorguIstegi) -> SorguYaniti:
    session_id = istek.session_id or uuid.uuid4().hex
    pipeline = get_pipeline()
    history = store.render_history(session_id)

    try:
        sonuc = pipeline.run(istek.soru, history=history, verbose=istek.verbose)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Pipeline hatası")
        raise HTTPException(status_code=500, detail=f"AI sorgulama başarısız: {exc}") from exc

    store.append(
        session_id,
        Turn(soru=sonuc.soru, sql=sonuc.uretilen_sql, cevap=sonuc.cevap),
    )

    debug_payload = None
    if istek.debug:
        debug_payload = {
            "duzeltme_logu": sonuc.duzeltme_logu,
            "intent": sonuc.structured.intent.value,
            "row_count": sonuc.structured.row_count,
            "columns": sonuc.structured.columns,
            "rows": sonuc.structured.rows[:50],
        }

    return SorguYaniti(
        soru=sonuc.soru,
        cevap=sonuc.cevap,
        uretilen_sql=sonuc.uretilen_sql,
        session_id=session_id,
        deneme_sayisi=sonuc.deneme_sayisi,
        debug=debug_payload,
    )


@app.post("/api/ai/chat", response_model=ChatYaniti)
def ai_chat(istek: SorguIstegi) -> ChatYaniti:
    session_id = istek.session_id or uuid.uuid4().hex
    orchestrator = get_chat_orchestrator()
    history = store.render_history(session_id)

    try:
        sonuc = orchestrator.run(
            istek.soru,
            history=history,
            verbose=istek.verbose,
        )
    except SlashCommandError as exc:
        raise HTTPException(
            status_code=400,
            detail={"message": str(exc), "allowed_commands": exc.allowed_commands},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Chat pipeline hatasÄ±")
        raise HTTPException(status_code=500, detail=f"AI chat baÅŸarÄ±sÄ±z: {exc}") from exc

    store.append(
        session_id,
        Turn(
            soru=sonuc.soru,
            sql="[DOCS]" if sonuc.route == ROUTE_DOCS else (sonuc.uretilen_sql or ""),
            cevap=sonuc.cevap,
        ),
    )

    debug_payload = None
    if istek.debug:
        debug_payload = dict(sonuc.debug)
        if sonuc.structured is not None:
            debug_payload.update(
                {
                    "duzeltme_logu": sonuc.duzeltme_logu or [],
                    "intent": sonuc.structured.intent.value,
                    "row_count": sonuc.structured.row_count,
                    "columns": sonuc.structured.columns,
                    "rows": sonuc.structured.rows[:50],
                }
            )

    return ChatYaniti(
        soru=sonuc.soru,
        cevap=sonuc.cevap,
        uretilen_sql=sonuc.uretilen_sql,
        session_id=session_id,
        deneme_sayisi=sonuc.deneme_sayisi,
        route=sonuc.route,
        route_source=sonuc.route_source,
        confidence=sonuc.confidence,
        sources=sonuc.sources,
        debug=debug_payload,
    )


@app.post("/api/ai/oturum/sifirla")
def oturum_sifirla(istek: OturumIstegi) -> dict:
    store.clear(istek.session_id)
    return {"status": "ok", "session_id": istek.session_id}


@app.get("/api/ai/sema")
def sema() -> dict:
    """Frontend'e şema açıklaması ve örnek soruları sergileyen yardımcı endpoint."""
    from prompts import FEW_SHOT_EXAMPLES

    return {
        "sema": SCHEMA_DESCRIPTION.strip(),
        "ornek_sorular": [ex["soru"] for ex in FEW_SHOT_EXAMPLES],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
