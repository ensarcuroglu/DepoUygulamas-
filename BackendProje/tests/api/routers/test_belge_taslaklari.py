from __future__ import annotations

import pytest

from app.core.config import get_settings
from models import BelgeTaslagi
from tests.factories import DepoFactory

pytestmark = pytest.mark.api

INTERNAL_KEY = "test-internal-doc-ai-key"


def _raw_payload(confidence: float = 0.45, missing_fields: list[str] | None = None) -> dict:
    return {
        "status": "ok",
        "belge_tipi": "TEXT_PDF",
        "model": "fake-doc-ai",
        "taslak": {
            "tedarikci": {"value": "ACME GIDA", "confidence": confidence},
            "irsaliye_no": {"value": "IRS-1", "confidence": confidence},
            "tarih": {"value": "2026-05-11", "confidence": confidence},
            "kalemler": [
                {
                    "urun_kodu": {"value": "ABC-1", "confidence": confidence},
                    "ad": {"value": "Pirinc", "confidence": confidence},
                    "miktar": {"value": 10, "confidence": confidence},
                    "birim": {"value": "KG", "confidence": confidence},
                }
            ],
            "missing_fields": missing_fields or [],
            "validation_errors": [],
            "confidence_score": confidence,
        },
    }


@pytest.fixture
def internal_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("INTERNAL_API_KEY", INTERNAL_KEY)
    get_settings.cache_clear()
    yield INTERNAL_KEY
    get_settings.cache_clear()


def _callback_payload(depo_id: int, confidence: float = 0.55) -> dict:
    return {
        "kaynak_dosya_yolu": "uploads/belge_taslaklari/test.pdf",
        "belge_tipi": "IRSALIYE",
        "ham_json": _raw_payload(confidence),
        "confidence_skoru": confidence,
        "depo_id": depo_id,
    }


def _create_taslak(db_session, *, depo_id: int, confidence: float, durum: str = "KABUL_BEKLIYOR"):
    taslak = BelgeTaslagi(
        kaynak_dosya_yolu=f"uploads/test-{confidence}.pdf",
        belge_tipi="IRSALIYE",
        ham_json=_raw_payload(confidence, missing_fields=["irsaliye_no"] if confidence < 0.6 else []),
        durum=durum,
        confidence_skoru=confidence,
        depo_id=depo_id,
    )
    db_session.add(taslak)
    db_session.commit()
    db_session.refresh(taslak)
    return taslak


def test_callback_returns_503_when_internal_key_is_not_configured(
    client,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    depo = DepoFactory.create()
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    get_settings.cache_clear()

    response = client.post(
        "/api/belge-taslaklari/",
        headers={"X-Internal-Api-Key": INTERNAL_KEY},
        json=_callback_payload(depo.id),
    )

    assert response.status_code == 503


def test_callback_rejects_wrong_internal_key(client, internal_key, db_session):
    depo = DepoFactory.create()

    response = client.post(
        "/api/belge-taslaklari/",
        headers={"X-Internal-Api-Key": "wrong"},
        json=_callback_payload(depo.id),
    )

    assert response.status_code == 401


def test_callback_flow_is_idempotent(client, internal_key, db_session):
    depo = DepoFactory.create()
    headers = {
        "X-Internal-Api-Key": internal_key,
        "Idempotency-Key": "doc-ai-callback-1",
    }

    first = client.post(
        "/api/belge-taslaklari/",
        headers=headers,
        json=_callback_payload(depo.id, confidence=0.52),
    )
    second = client.post(
        "/api/belge-taslaklari/",
        headers=headers,
        json=_callback_payload(depo.id, confidence=0.99),
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json() == second.json()
    assert db_session.query(BelgeTaslagi).count() == 1
    assert first.json()["confidence_skoru"] == 0.52


@pytest.mark.parametrize(
    ("client_fixture", "expected_status"),
    [
        ("client", 401),
        ("depocu_client", 403),
        ("admin_client", 200),
        ("lojistik_client", 200),
    ],
)
def test_inceleme_kuyrugu_auth_and_role(
    request,
    client_fixture,
    expected_status,
    db_session,
):
    depo = DepoFactory.create()
    _create_taslak(db_session, depo_id=depo.id, confidence=0.4)
    client = request.getfixturevalue(client_fixture)

    response = client.get("/api/belge-taslaklari/inceleme-kuyrugu")

    assert response.status_code == expected_status


def test_inceleme_kuyrugu_only_returns_pending_low_confidence(admin_client, db_session):
    depo = DepoFactory.create()
    low = _create_taslak(db_session, depo_id=depo.id, confidence=0.42)
    _create_taslak(db_session, depo_id=depo.id, confidence=0.85)
    _create_taslak(db_session, depo_id=depo.id, confidence=0.2, durum="KABUL_EDILDI")

    response = admin_client.get("/api/belge-taslaklari/inceleme-kuyrugu")

    assert response.status_code == 200, response.text
    data = response.json()
    assert [item["id"] for item in data] == [low.id]
    assert data[0]["confidence_skoru"] == 0.42
    assert data[0]["ham_json"]["taslak"]["missing_fields"] == ["irsaliye_no"]
