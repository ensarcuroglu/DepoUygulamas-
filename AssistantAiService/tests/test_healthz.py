"""Healthz + internal-auth davranisi."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.v1.routers import healthz as healthz_module
from app.core.config import get_settings
from main import app
from tests.conftest import TEST_KEY, TEST_MODEL


@pytest.fixture
def mock_ollama_ok(monkeypatch: pytest.MonkeyPatch):
    async def fake_fetch(settings):
        return {"models": [{"name": settings.assistant_llm_model}]}

    monkeypatch.setattr(healthz_module, "_fetch_ollama_tags", fake_fetch)


def test_healthz_valid_key_returns_200(mock_ollama_ok):
    with TestClient(app) as client:
        response = client.get("/healthz", headers={"X-Internal-Api-Key": TEST_KEY})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "AssistantAiService"
    assert body["ollama"]["assistant_model"] == TEST_MODEL
    assert body["ollama"]["assistant_model_available"] is True


def test_healthz_missing_key_returns_503(mock_ollama_ok):
    with TestClient(app) as client:
        response = client.get("/healthz")

    assert response.status_code == 503


def test_healthz_wrong_key_returns_503(mock_ollama_ok):
    with TestClient(app) as client:
        response = client.get("/healthz", headers={"X-Internal-Api-Key": "wrong"})

    assert response.status_code == 503


def test_healthz_unconfigured_internal_key_returns_503(
    monkeypatch: pytest.MonkeyPatch,
    mock_ollama_ok,
):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    get_settings.cache_clear()

    with TestClient(app) as client:
        response = client.get("/healthz", headers={"X-Internal-Api-Key": TEST_KEY})

    assert response.status_code == 503
    assert response.json()["detail"] == "Internal API kimligi yapilandirilmamis"


def test_healthz_ollama_unreachable_returns_503(monkeypatch: pytest.MonkeyPatch):
    async def fake_fetch(settings):
        request = httpx.Request("GET", settings.ollama_base_url.rstrip("/") + "/api/tags")
        raise httpx.ConnectError("connection failed", request=request)

    monkeypatch.setattr(healthz_module, "_fetch_ollama_tags", fake_fetch)

    with TestClient(app) as client:
        response = client.get("/healthz", headers={"X-Internal-Api-Key": TEST_KEY})

    assert response.status_code == 503
    assert response.json()["detail"] == "Ollama baglantisi basarisiz"


def test_healthz_missing_assistant_model_returns_503(monkeypatch: pytest.MonkeyPatch):
    async def fake_fetch(settings):
        return {"models": [{"name": "baska-model:latest"}]}

    monkeypatch.setattr(healthz_module, "_fetch_ollama_tags", fake_fetch)

    with TestClient(app) as client:
        response = client.get("/healthz", headers={"X-Internal-Api-Key": TEST_KEY})

    assert response.status_code == 503
    assert response.json()["detail"] == f"Ollama asistan modeli bulunamadi: {TEST_MODEL}"
