"""Hybrid extraction use case that routes text PDFs and visual documents."""

from __future__ import annotations

from dataclasses import dataclass

from app.application.use_cases.text_pdf_extract_uc import (
    FileTooLargeError,
    UnsupportedDocumentTypeError,
)
from app.core.entities.belge import Belge, BelgeTipi, ExtractionSonucu
from app.core.services.belge_tipi_dedektoru import BelgeTipiDedektoru
from app.infrastructure.extraction.text_pdf_extractor import TextPdfExtractor
from app.infrastructure.extraction.vlm_extractor import VlmExtractor


@dataclass(frozen=True)
class HibritExtractUseCase:
    max_file_size_mb: int
    detector: BelgeTipiDedektoru
    text_extractor: TextPdfExtractor
    vlm_extractor: VlmExtractor

    async def execute(
        self,
        *,
        filename: str,
        content_type: str | None,
        content: bytes,
    ) -> ExtractionSonucu:
        max_bytes = self.max_file_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise FileTooLargeError(
                f"Dosya boyutu {self.max_file_size_mb} MB limitini asiyor"
            )

        belge = Belge(filename=filename, content_type=content_type, content=content)
        belge_tipi = self.detector.detect(belge)

        if belge_tipi is BelgeTipi.TEXT_PDF:
            return await self.text_extractor.extract(belge)
        if belge_tipi in {BelgeTipi.SCANNED_PDF, BelgeTipi.IMAGE}:
            return await self.vlm_extractor.extract(belge, belge_tipi=belge_tipi)

        raise UnsupportedDocumentTypeError(f"Desteklenmeyen belge tipi: {belge_tipi.value}")
