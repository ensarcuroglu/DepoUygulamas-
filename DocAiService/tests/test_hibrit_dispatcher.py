"""Hybrid dispatcher tests for Faz 2."""

from __future__ import annotations

import asyncio

import pytest

from app.application.use_cases.hibrit_extract_uc import HibritExtractUseCase
from app.core.entities.belge import Belge, BelgeTipi, ExtractionSonucu
from app.core.entities.irsaliye_taslagi import IrsaliyeTaslagiSchema


def sample_taslak() -> IrsaliyeTaslagiSchema:
    return IrsaliyeTaslagiSchema.model_validate(
        {
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
    )


class FakeDetector:
    def __init__(self, belge_tipi: BelgeTipi) -> None:
        self.belge_tipi = belge_tipi

    def detect(self, belge: Belge) -> BelgeTipi:
        return self.belge_tipi


class FakeTextExtractor:
    def __init__(self) -> None:
        self.calls = 0

    async def extract(self, belge: Belge) -> ExtractionSonucu:
        self.calls += 1
        return ExtractionSonucu(
            belge_tipi=BelgeTipi.TEXT_PDF,
            taslak=sample_taslak(),
            raw_text="text",
            model="text-model",
        )


class FakeVlmExtractor:
    def __init__(self) -> None:
        self.calls = 0

    async def extract(self, belge: Belge, *, belge_tipi: BelgeTipi) -> ExtractionSonucu:
        self.calls += 1
        return ExtractionSonucu(
            belge_tipi=belge_tipi,
            taslak=sample_taslak(),
            raw_text="",
            model="vlm-model",
        )


def test_hibrit_dispatcher_routes_text_pdf_to_text_extractor():
    text_extractor = FakeTextExtractor()
    vlm_extractor = FakeVlmExtractor()
    uc = HibritExtractUseCase(
        max_file_size_mb=25,
        detector=FakeDetector(BelgeTipi.TEXT_PDF),
        text_extractor=text_extractor,
        vlm_extractor=vlm_extractor,
    )

    result = asyncio.run(
        uc.execute(
            filename="irsaliye.pdf",
            content_type="application/pdf",
            content=b"%PDF text",
        )
    )

    assert result.belge_tipi is BelgeTipi.TEXT_PDF
    assert result.model == "text-model"
    assert text_extractor.calls == 1
    assert vlm_extractor.calls == 0


@pytest.mark.parametrize("belge_tipi", [BelgeTipi.SCANNED_PDF, BelgeTipi.IMAGE])
def test_hibrit_dispatcher_routes_visual_documents_to_vlm(belge_tipi: BelgeTipi):
    text_extractor = FakeTextExtractor()
    vlm_extractor = FakeVlmExtractor()
    uc = HibritExtractUseCase(
        max_file_size_mb=25,
        detector=FakeDetector(belge_tipi),
        text_extractor=text_extractor,
        vlm_extractor=vlm_extractor,
    )

    result = asyncio.run(
        uc.execute(
            filename="irsaliye.jpg",
            content_type="image/jpeg",
            content=b"image",
        )
    )

    assert result.belge_tipi is belge_tipi
    assert result.model == "vlm-model"
    assert text_extractor.calls == 0
    assert vlm_extractor.calls == 1
