"""Faz 1 text PDF extraction tests."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routers import extraction as extraction_module
from app.application.use_cases.text_pdf_extract_uc import (
    TextPdfExtractUseCase,
    UnsupportedDocumentTypeError,
)
from app.core.config import get_settings
from app.core.entities.belge import Belge, BelgeTipi, ExtractionSonucu
from app.core.entities.irsaliye_taslagi import IrsaliyeTaslagiSchema
from app.infrastructure.extraction.text_pdf_extractor import TextPdfExtractor
from app.infrastructure.llm.ollama_text_client import _parse_json_content
from main import app

TEST_KEY = "test-internal-key"
FIXTURE_PATH = Path(__file__).parent / "fixtures" / "irsaliye_text_pdf.pdf"


def sample_payload() -> dict:
    return {
        "tedarikci": {"value": "ACME GIDA A.S.", "confidence": 0.95},
        "irsaliye_no": {"value": "IRS-2026-0001", "confidence": 0.91},
        "tarih": {"value": "2026-05-11", "confidence": 0.93},
        "kalemler": [
            {
                "urun_kodu": {"value": "URUN-001", "confidence": 0.87},
                "ad": {"value": "Pirinc", "confidence": 0.82},
                "miktar": {"value": 10, "confidence": 0.89},
                "birim": {"value": "KG", "confidence": 0.9},
            }
        ],
        "toplam": {"value": 10, "confidence": 0.88},
    }


@pytest.fixture(autouse=True)
def settings_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("INTERNAL_API_KEY", TEST_KEY)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setenv("OLLAMA_TEXT_MODEL", "qwen3-vl:4b")
    get_settings.cache_clear()
    extraction_module._IDEMPOTENCY_CACHE.clear()
    yield
    app.dependency_overrides.clear()
    extraction_module._IDEMPOTENCY_CACHE.clear()
    get_settings.cache_clear()


def test_irsaliye_schema_validates_confidence_fields():
    taslak = IrsaliyeTaslagiSchema.model_validate(sample_payload())

    assert taslak.tedarikci.value == "ACME GIDA A.S."
    assert taslak.irsaliye_no.confidence > 0.7
    assert taslak.kalemler[0].miktar.value == 10
    assert taslak.confidence_score > 0.85


def test_parse_json_content_accepts_fenced_json():
    parsed = _parse_json_content('```json\n{"tedarikci": {"value": "A", "confidence": 0.8}}\n```')

    assert parsed["tedarikci"]["value"] == "A"


def test_text_pdf_extractor_maps_llm_payload(monkeypatch: pytest.MonkeyPatch):
    class FakeLlmClient:
        model = "fake-model"

        async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict:
            assert "JSON semasi" in system_prompt
            assert "ACME GIDA" in user_prompt
            return sample_payload()

    monkeypatch.setattr(
        TextPdfExtractor,
        "_extract_text",
        staticmethod(lambda content: "Tedarikci: ACME GIDA A.S."),
    )

    extractor = TextPdfExtractor(FakeLlmClient())
    result = asyncio.run(
        extractor.extract(
            Belge(
                filename="irsaliye_text_pdf.pdf",
                content_type="application/pdf",
                content=FIXTURE_PATH.read_bytes(),
            )
        )
    )

    assert result.belge_tipi is BelgeTipi.TEXT_PDF
    assert result.taslak.tedarikci.confidence > 0.7
    assert result.model == "fake-model"


def test_text_pdf_use_case_rejects_non_text_pdf():
    class FakeDetector:
        def detect(self, belge: Belge) -> BelgeTipi:
            return BelgeTipi.IMAGE

    class FakeExtractor:
        async def extract(self, belge: Belge) -> ExtractionSonucu:  # pragma: no cover
            raise AssertionError("extractor should not be called")

    uc = TextPdfExtractUseCase(
        max_file_size_mb=25,
        detector=FakeDetector(),
        extractor=FakeExtractor(),
    )

    with pytest.raises(UnsupportedDocumentTypeError):
        asyncio.run(
            uc.execute(
                filename="foto.jpg",
                content_type="image/jpeg",
                content=b"not a pdf",
            )
        )


def test_extract_irsaliye_endpoint_returns_schema_with_idempotency():
    taslak = IrsaliyeTaslagiSchema.model_validate(sample_payload())

    class FakeUseCase:
        calls = 0

        async def execute(self, *, filename: str, content_type: str | None, content: bytes):
            self.calls += 1
            assert filename == "irsaliye_text_pdf.pdf"
            assert content_type == "application/pdf"
            assert content
            return ExtractionSonucu(
                belge_tipi=BelgeTipi.TEXT_PDF,
                taslak=taslak,
                raw_text="Tedarikci: ACME GIDA A.S.",
                model="fake-model",
            )

    fake_uc = FakeUseCase()
    app.dependency_overrides[extraction_module.get_text_pdf_extract_uc] = lambda: fake_uc

    headers = {
        "X-Internal-Api-Key": TEST_KEY,
        "Idempotency-Key": "idem-1",
    }
    files = {
        "file": (
            "irsaliye_text_pdf.pdf",
            FIXTURE_PATH.read_bytes(),
            "application/pdf",
        )
    }
    with TestClient(app) as client:
        first = client.post("/api/extract/irsaliye", headers=headers, files=files)
        second = client.post("/api/extract/irsaliye", headers=headers, files=files)

    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json() == second.json()
    assert fake_uc.calls == 1

    body = first.json()
    assert body["status"] == "ok"
    assert body["belge_tipi"] == "TEXT_PDF"
    assert body["idempotency_key"] == "idem-1"

    taslak_body = body["taslak"]
    confidences = [
        taslak_body["tedarikci"]["confidence"],
        taslak_body["irsaliye_no"]["confidence"],
        taslak_body["tarih"]["confidence"],
        taslak_body["kalemler"][0]["urun_kodu"]["confidence"],
    ]
    assert sum(value > 0.7 for value in confidences) >= 3
