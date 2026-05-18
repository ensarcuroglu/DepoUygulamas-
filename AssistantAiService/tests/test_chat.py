"""Chat endpoint contract tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from main import app
from tests.conftest import TEST_KEY


def _payload(session_id: str | None = "s1") -> dict:
    return {
        "soru": "Stok durumunu ozetler misin?",
        "session_id": session_id,
        "user_context": {
            "kullanici_id": 7,
            "rol": "depocu",
            "aktif_gorev_id": None,
            "aktif_ekran": "terminal",
            "izinli_tool_idleri": ["stok_sorgula"],
        },
    }


def test_chat_valid_key_returns_backend_contract():
    with TestClient(app) as client:
        response = client.post(
            "/api/asistan/chat",
            json=_payload(),
            headers={"X-Internal-Api-Key": TEST_KEY},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["cevap"]
    assert body["session_id"] == "s1"
    assert body["proposed_action"] is None
    assert body["debug"]["mode"] == "contract_ready"


def test_chat_generates_session_id_when_missing():
    with TestClient(app) as client:
        response = client.post(
            "/api/asistan/chat",
            json=_payload(session_id=None),
            headers={"X-Internal-Api-Key": TEST_KEY},
        )

    assert response.status_code == 200
    assert response.json()["session_id"]


def test_chat_missing_internal_key_returns_503():
    with TestClient(app) as client:
        response = client.post("/api/asistan/chat", json=_payload())

    assert response.status_code == 503
