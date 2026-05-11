"""Document type detection for the extraction dispatcher."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from app.core.entities.belge import Belge, BelgeTipi


class BelgeTipiAlgilamaError(RuntimeError):
    """Raised when a PDF cannot be inspected."""


class BelgeTipiDedektoru:
    def __init__(self, min_text_chars: int = 20, max_pages: int = 3) -> None:
        self.min_text_chars = min_text_chars
        self.max_pages = max_pages

    def detect(self, belge: Belge) -> BelgeTipi:
        if self._is_pdf(belge):
            return self._detect_pdf(belge)
        return BelgeTipi.IMAGE

    def _detect_pdf(self, belge: Belge) -> BelgeTipi:
        text = self._extract_pdf_text_sample(belge.content)
        if len(text.strip()) >= self.min_text_chars:
            return BelgeTipi.TEXT_PDF
        return BelgeTipi.SCANNED_PDF

    def _extract_pdf_text_sample(self, content: bytes) -> str:
        try:
            import pdfplumber
        except ImportError as exc:
            raise BelgeTipiAlgilamaError("pdfplumber kurulu degil") from exc

        try:
            with pdfplumber.open(BytesIO(content)) as pdf:
                texts = []
                for page in pdf.pages[: self.max_pages]:
                    texts.append(page.extract_text() or "")
                return "\n".join(texts)
        except Exception as exc:  # noqa: BLE001
            raise BelgeTipiAlgilamaError("PDF metin ornegi okunamadi") from exc

    @staticmethod
    def _is_pdf(belge: Belge) -> bool:
        content_type = (belge.content_type or "").lower()
        suffix = Path(belge.filename).suffix.lower()
        return content_type == "application/pdf" or suffix == ".pdf"
