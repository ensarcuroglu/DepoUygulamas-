"""Pytest fixture'ları — DataGenService."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Testler sırasında .env dosyasını ve cache'i devre dışı bırakır."""
    monkeypatch.setenv("DATA_GEN_ENV_FILE", os.devnull)
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture()
def client() -> TestClient:
    from main import app

    return TestClient(app)
