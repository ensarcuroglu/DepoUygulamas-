"""Visual document extraction using an Ollama multimodal model."""

from __future__ import annotations

from pydantic import ValidationError

from app.application.prompts import SYSTEM_PROMPT, VLM_IRSALIYE_PROMPT
from app.core.entities.belge import Belge, BelgeTipi, ExtractionSonucu
from app.core.entities.irsaliye_taslagi import IrsaliyeTaslagiSchema
from app.core.services.confidence_calculator import normalize_irsaliye_confidence
from app.infrastructure.extraction.image_renderer import ImageRenderer
from app.infrastructure.llm.ollama_vlm_client import OllamaVlmClient


class VlmExtractionError(RuntimeError):
    """Raised when VLM extraction or schema parsing fails."""


class VlmExtractor:
    def __init__(self, llm_client: OllamaVlmClient, renderer: ImageRenderer) -> None:
        self.llm_client = llm_client
        self.renderer = renderer

    async def extract(self, belge: Belge, *, belge_tipi: BelgeTipi) -> ExtractionSonucu:
        rendered = self.renderer.render(belge, belge_tipi)
        payload = await self.llm_client.chat_image_json(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=VLM_IRSALIYE_PROMPT,
            image_base64=rendered.image_base64,
        )
        normalized_payload = normalize_irsaliye_confidence(payload)
        normalized_payload.pop("confidence_score", None)
        try:
            taslak = IrsaliyeTaslagiSchema.model_validate(normalized_payload)
        except ValidationError as exc:
            raise VlmExtractionError("VLM yaniti irsaliye semasina uymuyor") from exc

        return ExtractionSonucu(
            belge_tipi=belge_tipi,
            taslak=taslak,
            raw_text="",
            model=self.llm_client.model,
            metadata={
                "image_width": rendered.width,
                "image_height": rendered.height,
                "image_mime_type": rendered.mime_type,
                "page_index": rendered.page_index,
            },
        )
