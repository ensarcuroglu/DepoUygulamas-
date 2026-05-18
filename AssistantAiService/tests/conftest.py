"""Shared test fixtures for AssistantAiService."""

from __future__ import annotations

import pytest

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
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
