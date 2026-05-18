"""Chat endpoint behavior tests (HTTP surface).

Faz 2: placeholder yerine gercek graph cagiriliyor. TestClient ile end-to-end
HTTP yuzeyi: oturum id uretimi, fake LLM ile plain cevap, HITL kestiriminde
proposed_action dolumu, internal-api-key kontrolu.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api.v1.routers.asistan import get_graph
from main import app
from tests.conftest import TEST_KEY, make_ai, make_fake_model


def _payload(soru: str = "Stok durumunu ozetler misin?", session_id: str | None = "s1") -> dict:
    return {
        "soru": soru,
        "session_id": session_id,
        "user_context": {
            "kullanici_id": 7,
            "rol": "depocu",
            "aktif_gorev_id": None,
            "aktif_ekran": "terminal",
            "izinli_tool_idleri": ["tarih_saat_simdi", "yerlestirme_konum_degistir"],
        },
    }


# ---------------------------------------------------------------------------
# Plain text reply
# ---------------------------------------------------------------------------

def test_chat_plain_text_returns_llm_cevap(chat_client: TestClient):
    response = chat_client.post(
        "/api/asistan/chat",
        json=_payload(),
        headers={"X-Internal-Api-Key": TEST_KEY},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cevap"] == "merhaba (test)"
    assert body["session_id"] == "s1"
    assert body["proposed_action"] is None


def test_chat_generates_session_id_when_missing(chat_client: TestClient):
    response = chat_client.post(
        "/api/asistan/chat",
        json=_payload(session_id=None),
        headers={"X-Internal-Api-Key": TEST_KEY},
    )
    assert response.status_code == 200
    sid = response.json()["session_id"]
    assert isinstance(sid, str) and len(sid) >= 8


def test_chat_missing_internal_key_returns_503():
    # Override yapilmadigindan lifespan-built graph kullanilir; ama middleware
    # daha onceden 503 dondurur.
    with TestClient(app) as client:
        response = client.post("/api/asistan/chat", json=_payload())
    assert response.status_code == 503


# ---------------------------------------------------------------------------
# HITL short-circuit via HTTP
# ---------------------------------------------------------------------------

def test_chat_hitl_tool_call_returns_proposed_action(make_graph):
    """LLM HITL aleti secince proposed_action dolumlanmali, durum BEKLEMEDE'de bos."""
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[
                    {
                        "name": "yerlestirme_konum_degistir",
                        "id": "tc1",
                        "args": {"gorev_id": 42, "yeni_konum_kodu": "B-12-3"},
                    }
                ],
            )
        ]
    )
    graph = make_graph(fake)
    app.dependency_overrides[get_graph] = lambda: graph
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/asistan/chat",
                json=_payload(soru="A koridoru tikali"),
                headers={"X-Internal-Api-Key": TEST_KEY},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    proposed = body["proposed_action"]
    assert proposed is not None
    assert proposed["tool_id"] == "yerlestirme_konum_degistir"
    assert proposed["params"] == {"gorev_id": 42, "yeni_konum_kodu": "B-12-3"}
    assert "B-12-3" in (proposed["ozet"] or "")
    # Cevap ici bos (LLM tool_call'da metin yazmadi); fallback metni doner.
    assert "onerdim" in body["cevap"].lower() or body["cevap"].endswith("reddedin.")
