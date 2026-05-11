"""Confidence scoring tests for Faz 6."""

from __future__ import annotations

import asyncio

from app.core.entities.belge import Belge, BelgeTipi
from app.core.services.confidence_calculator import ConfidenceCalculator
from app.infrastructure.extraction.text_pdf_extractor import TextPdfExtractor


def test_confidence_calculator_sets_zero_for_missing_fields():
    result = ConfidenceCalculator().normalize_irsaliye(
        {
            "tedarikci": {"value": "ACME GIDA", "confidence": 0.9},
            "kalemler": [
                {
                    "urun_kodu": {"value": "ABC-1", "confidence": 0.8},
                    "miktar": {"value": 10, "confidence": 0.7},
                    "birim": {"value": "", "confidence": 0.6},
                }
            ],
        }
    )

    assert result["irsaliye_no"]["confidence"] == 0.0
    assert result["tarih"]["value"] is None
    assert result["kalemler"][0]["ad"]["confidence"] == 0.0
    assert result["kalemler"][0]["birim"]["confidence"] == 0.0
    assert "irsaliye_no" in result["missing_fields"]
    assert "kalemler[0].ad" in result["missing_fields"]
    assert result["validation_errors"]
    assert result["confidence_score"] < 0.6


def test_confidence_calculator_averages_field_scores_and_clamps_values():
    result = ConfidenceCalculator().normalize_irsaliye(
        {
            "tedarikci": {"value": "ACME", "confidence": 1.2},
            "irsaliye_no": {"value": "IRS-1", "confidence": 0.8},
            "tarih": {"value": "2026-05-11", "confidence": 0.6},
            "kalemler": [
                {
                    "urun_kodu": {"value": "P-1", "confidence": 0.4},
                    "ad": {"value": "Pirinc", "confidence": 0.2},
                    "miktar": {"value": 5, "confidence": -1},
                    "birim": {"value": "KG", "confidence": 0.5},
                }
            ],
        }
    )

    assert result["tedarikci"]["confidence"] == 1.0
    assert result["kalemler"][0]["miktar"]["confidence"] == 0.0
    assert result["confidence_score"] == round((1.0 + 0.8 + 0.6 + 0.4 + 0.2 + 0.0 + 0.5) / 7, 4)
    assert result["missing_fields"] == []


def test_text_pdf_extractor_returns_validation_errors_in_schema(monkeypatch):
    class FakeLlmClient:
        model = "fake-model"

        async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict:
            return {
                "tedarikci": {"value": "ACME GIDA", "confidence": 0.9},
                "irsaliye_no": {"value": "", "confidence": 0.8},
                "tarih": {"value": "2026-05-11", "confidence": 0.9},
                "kalemler": [],
            }

    monkeypatch.setattr(
        TextPdfExtractor,
        "_extract_text",
        staticmethod(lambda content: "Tedarikci: ACME GIDA"),
    )

    result = asyncio.run(
        TextPdfExtractor(FakeLlmClient()).extract(
            Belge(filename="irsaliye.pdf", content_type="application/pdf", content=b"%PDF")
        )
    )

    assert result.belge_tipi is BelgeTipi.TEXT_PDF
    assert result.taslak.irsaliye_no.confidence == 0.0
    assert result.taslak.validation_errors == [
        "irsaliye_no alani eksik veya bos",
        "kalemler alani eksik veya bos",
    ]
