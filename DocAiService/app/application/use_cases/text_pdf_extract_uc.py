"""Text PDF extraction use case."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.entities.belge import Belge, BelgeTipi, ExtractionSonucu
from app.core.services.belge_tipi_dedektoru import BelgeTipiDedektoru
from app.infrastructure.extraction.text_pdf_extractor import TextPdfExtractor


class FileTooLargeError(ValueError):
    """Raised when an uploaded file exceeds the configured maximum size."""


class UnsupportedDocumentTypeError(ValueError):
    """Raised when Faz 1 cannot process the detected document type."""


@dataclass(frozen=True)
class TextPdfExtractUseCase:
    max_file_size_mb: int
    detector: BelgeTipiDedektoru
    extractor: TextPdfExtractor

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
        if belge_tipi is not BelgeTipi.TEXT_PDF:
            raise UnsupportedDocumentTypeError(
                f"Faz 1 yalnizca text PDF destekler; algilanan tip={belge_tipi.value}"
            )

        return await self.extractor.extract(belge)
