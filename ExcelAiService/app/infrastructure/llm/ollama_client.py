"""Ollama LLM client factory'leri.

LangChain ekosisteminde Ollama'ya `langchain-ollama` ile baglaniyoruz.
Bu modul tek noktada konfigurasyonlu `ChatOllama` instance'i uretir;
agent ve template-first kullanim ayni LLM'i paylasir.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from langchain_ollama import ChatOllama

from app.core.config import Settings

log = logging.getLogger(__name__)


def build_chat_llm(settings: Settings, *, temperature: float = 0.0) -> ChatOllama:
    """ChatOllama instance uret. Pandas agent ve yorum cagrilari icin paylasilir."""
    log.debug(
        "ChatOllama olusturuluyor: base=%s model=%s timeout=%s",
        settings.ollama_base_url,
        settings.ollama_text_model,
        settings.llm_timeout,
    )
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_text_model,
        temperature=temperature,
        timeout=settings.llm_timeout,
    )


@lru_cache(maxsize=4)
def _cached_chat_llm(
    base_url: str,
    model: str,
    timeout: float,
    temperature: float,
) -> ChatOllama:
    return ChatOllama(
        base_url=base_url,
        model=model,
        timeout=timeout,
        temperature=temperature,
    )


def get_chat_llm(settings: Settings, *, temperature: float = 0.0) -> ChatOllama:
    """Yeniden kullanilabilir cache'li ChatOllama getirici."""
    return _cached_chat_llm(
        settings.ollama_base_url,
        settings.ollama_text_model,
        settings.llm_timeout,
        temperature,
    )
