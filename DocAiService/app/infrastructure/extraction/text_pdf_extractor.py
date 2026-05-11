"""Text PDF extraction implementation."""

from __future__ import annotations

from io import BytesIO

from pydantic import ValidationError

from app.application.prompts import SYSTEM_PROMPT, build_irsaliye_text_prompt
from app.core.entities.belge import Belge, BelgeTipi, ExtractionSonucu
from app.core.entities.irsaliye_taslagi import IrsaliyeTaslagiSchema
from app.core.services.confidence_calculator import normalize_irsaliye_confidence
from app.infrastructure.llm.ollama_text_client import OllamaTextClient


class TextPdfExtractionError(RuntimeError):
    """Raised when text extraction or schema parsing fails."""


class TextPdfExtractor:
    def __init__(self, llm_client: OllamaTextClient) -> None:
        self.llm_client = llm_client

    async def extract(self, belge: Belge) -> ExtractionSonucu:
        raw_text = self._extract_text(belge.content)
        if not raw_text.strip():
            raise TextPdfExtractionError("PDF icinden metin okunamadi")

        payload = await self.llm_client.chat_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=build_irsaliye_text_prompt(raw_text),
        )
        normalized_payload = normalize_irsaliye_confidence(payload)
        normalized_payload.pop("confidence_score", None)
        try:
            taslak = IrsaliyeTaslagiSchema.model_validate(normalized_payload)
        except ValidationError as exc:
            raise TextPdfExtractionError("LLM yaniti irsaliye semasina uymuyor") from exc

        return ExtractionSonucu(
            belge_tipi=BelgeTipi.TEXT_PDF,
            taslak=taslak,
            raw_text=raw_text,
            model=self.llm_client.model,
            metadata={"raw_text_length": len(raw_text)},
        )

    @staticmethod
    def _extract_text(content: bytes) -> str:
        try:
            import pdfplumber
        except ImportError as exc:
            raise TextPdfExtractionError("pdfplumber kurulu degil") from exc

        try:
            with pdfplumber.open(BytesIO(content)) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as exc:  # noqa: BLE001
            raise TextPdfExtractionError("PDF metni okunamadi") from exc
