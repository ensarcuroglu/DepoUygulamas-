"""Faz 1 smoke testleri."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_healthz_returns_ok(client: TestClient) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "data-gen"}


@pytest.mark.unit
def test_settings_defaults_are_sane() -> None:
    from app.core.config import get_settings

    settings = get_settings()
    assert settings.batch_size == 500
    assert settings.concurrency == 10
    assert settings.default_seed == 42
    assert settings.locale == "tr_TR"
    assert settings.rabbitmq_exchange == "depo.events"
    assert settings.backend_base_url.startswith("http")
