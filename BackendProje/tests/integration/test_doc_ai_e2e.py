from __future__ import annotations

import pytest

from app.api.v1.routers import mal_kabul as mal_kabul_module
from app.core.config import get_settings
from main import app
from models import BelgeTaslagi, MalKabulIrsaliye
from tests.factories import DepoFactory, TedarikciFactory, UrunFactory

pytestmark = pytest.mark.integration


class FakeDocAiClient:
    def __init__(self, *, urun_kodu: str):
        self.urun_kodu = urun_kodu
        self.calls = 0

    def extract_irsaliye(
        self,
        *,
        filename: str,
        content_type: str | None,
        content: bytes,
        idempotency_key: str | None = None,
    ) -> dict:
        self.calls += 1
        assert filename == "irsaliye.pdf"
        assert content_type == "application/pdf"
        assert content
        assert idempotency_key == "doc-ai-e2e"
        return {
            "status": "ok",
            "belge_tipi": "TEXT_PDF",
            "model": "fake-doc-ai",
            "taslak": {
                "tedarikci": {"value": "ACME GIDA", "confidence": 0.92},
                "irsaliye_no": {"value": "IRS-E2E-1", "confidence": 0.91},
                "tarih": {"value": "2026-05-11", "confidence": 0.9},
                "kalemler": [
                    {
                        "urun_kodu": {"value": self.urun_kodu, "confidence": 0.88},
                        "ad": {"value": "Pirinc", "confidence": 0.86},
                        "miktar": {"value": 7, "confidence": 0.87},
                        "birim": {"value": "KG", "confidence": 0.89},
                    }
                ],
                "missing_fields": [],
                "validation_errors": [],
                "confidence_score": 0.89,
            },
        }


def test_doc_ai_upload_to_mal_kabul_e2e(
    admin_client,
    db_session,
    monkeypatch: pytest.MonkeyPatch,
):
    depo = DepoFactory.create(isim="DocAI E2E Depo")
    TedarikciFactory.create(firma_adi="ACME GIDA")
    urun = UrunFactory.create(isim="Pirinc", barkod="DOC-AI-001", ean="DOC-AI-EAN")
    fake_client = FakeDocAiClient(urun_kodu=urun.barkod)

    monkeypatch.setenv("FEATURE_DOC_AI_PILOT_DEPO_IDS", str(depo.id))
    get_settings.cache_clear()
    monkeypatch.setattr(
        mal_kabul_module,
        "_store_upload",
        lambda content, filename: "uploads/belge_taslaklari/test-e2e.pdf",
    )
    app.dependency_overrides[mal_kabul_module.get_doc_ai_client] = lambda: fake_client

    try:
        upload = admin_client.post(
            "/api/mal-kabul/belge-yukle",
            headers={"Idempotency-Key": "doc-ai-e2e"},
            data={"depo_id": str(depo.id)},
            files={"file": ("irsaliye.pdf", b"%PDF-1.4 fake text pdf", "application/pdf")},
        )

        assert upload.status_code == 201, upload.text
        taslak_id = upload.json()["id"]

        detail = admin_client.get(f"/api/belge-taslaklari/{taslak_id}")
        assert detail.status_code == 200
        assert detail.json()["ham_json"]["taslak"]["tedarikci"]["value"] == "ACME GIDA"

        approved = admin_client.post(f"/api/belge-taslaklari/{taslak_id}/onayla", json={})

        assert approved.status_code == 200, approved.text
        approved_body = approved.json()
        assert approved_body["durum"] == "KABUL_EDILDI"
        assert approved_body["mal_kabul_irsaliye_id"] is not None
        assert fake_client.calls == 1
        assert db_session.query(BelgeTaslagi).count() == 1
        assert db_session.query(MalKabulIrsaliye).count() == 1
    finally:
        app.dependency_overrides.pop(mal_kabul_module.get_doc_ai_client, None)
        get_settings.cache_clear()
