"""Shared test fixtures for AssistantAiService."""

from __future__ import annotations

from typing import Iterable

import pytest
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage, BaseMessage

from app.application.agent.graph import build_graph
from app.application.agent.tools import LocalToolRegistry, default_registry
from app.core.config import get_settings

TEST_KEY = "test-internal-key"
TEST_MODEL = "qwen2.5-coder:7b"


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch: pytest.MonkeyPatch):
    """Every test starts with a fresh, predictable Settings instance."""
    monkeypatch.setenv("ASSISTANT_AI_ENV_FILE", "__test_missing.env")
    monkeypatch.setenv("INTERNAL_API_KEY", TEST_KEY)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setenv("ASSISTANT_LLM_MODEL", TEST_MODEL)
    monkeypatch.setenv("BACKEND_BASE_URL", "http://backend.test")
    # Test'ler diske SQLite yazmasin diye in-memory checkpointer kullan.
    monkeypatch.setenv("SQLITE_CHECKPOINT_PATH", ":memory:")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ---------------------------------------------------------------------------
# Fake LLM
# ---------------------------------------------------------------------------

class FakeChatModel(FakeMessagesListChatModel):
    """FakeMessagesListChatModel + bind_tools no-op.

    Gercek ChatOllama bind_tools'la tool sema enjekte eder; bizim fake'imiz
    LLM'in *donen* mesajlarini kontrol etmek istedigi icin tool secimini
    test setup'i belirler (responses listesi). bind_tools cagrisi
    NotImplementedError yerine self doner.
    """

    def bind_tools(self, tools, **kwargs):  # type: ignore[override]
        return self


def make_fake_model(responses: Iterable[BaseMessage]) -> FakeChatModel:
    return FakeChatModel(responses=list(responses))


def make_ai(content: str = "", tool_calls: list[dict] | None = None) -> AIMessage:
    """Convenience constructor for fake LLM responses."""
    return AIMessage(content=content, tool_calls=tool_calls or [])


# ---------------------------------------------------------------------------
# Graph & app fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_registry() -> LocalToolRegistry:
    """Default registry rebuilt fresh per test (avoid singleton bleed)."""
    from app.application.agent import tools as tools_mod

    tools_mod.reset_default_registry()
    return default_registry()


@pytest.fixture
def make_graph(fresh_registry):
    """Factory: build a graph with a given fake LLM and optional checkpointer."""

    def _build(model: FakeChatModel, *, checkpointer=None):
        return build_graph(model, registry=fresh_registry, checkpointer=checkpointer)

    return _build


@pytest.fixture
def chat_client(make_graph):
    """TestClient with `get_graph` overridden to return a fake-graph.

    Default model: single plain-text AIMessage. Tests can override the
    `responses` parameter by re-overriding the dependency mid-test, but a
    cleaner pattern is to use `make_graph` directly and skip TestClient
    (see test_agent_graph.py).
    """
    from fastapi.testclient import TestClient

    from app.api.v1.routers.asistan import get_graph
    from main import app

    model = make_fake_model([make_ai(content="merhaba (test)")])
    test_graph = make_graph(model)
    app.dependency_overrides[get_graph] = lambda: test_graph

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
