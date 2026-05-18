"""ChatOllama factory.

Tek sorumluluk: ayarlardan ChatOllama instance uretmek. Test'lerde bu factory
monkeypatchlenir ya da `build_graph(llm=...)` argumani uzerinden FakeListChatModel
gibi sahte modeller enjekte edilir.
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from app.core.config import Settings, get_settings


def build_chat_model(settings: Settings | None = None) -> BaseChatModel:
    """Construct a fresh ChatOllama bound to project settings."""
    settings = settings or get_settings()
    return ChatOllama(
        model=settings.assistant_llm_model,
        base_url=settings.ollama_base_url,
        temperature=0,
        # ChatOllama uses request_timeout for HTTP and num_predict for generation length.
        # We leave generation length to the model default; HTTP timeout is bounded.
        timeout=settings.llm_timeout,
    )


@lru_cache(maxsize=1)
def get_chat_model() -> BaseChatModel:
    """Process-wide singleton chat model.

    Cached so multiple graph nodes share the same HTTP client / connection pool.
    Tests should NOT rely on the cache — they construct a fake model and pass it
    into `build_graph` directly.
    """
    return build_chat_model()
