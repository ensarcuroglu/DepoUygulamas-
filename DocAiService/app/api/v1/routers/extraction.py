"""Document extraction endpoints."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.application.use_cases.hibrit_extract_uc import HibritExtractUseCase
from app.application.use_cases.text_pdf_extract_uc import (
    FileTooLargeError,
    UnsupportedDocumentTypeError,
)
from app.core.config import Settings, get_settings
from app.core.entities.belge import BelgeTipi
from app.core.entities.irsaliye_taslagi import IrsaliyeTaslagiSchema
from app.core.services.belge_tipi_dedektoru import BelgeTipiAlgilamaError, BelgeTipiDedektoru
from app.infrastructure.extraction.image_renderer import ImageRenderer, ImageRenderingError
from app.infrastructure.extraction.text_pdf_extractor import (
    TextPdfExtractionError,
    TextPdfExtractor,
)
from app.infrastructure.extraction.vlm_extractor import VlmExtractionError, VlmExtractor
from app.infrastructure.llm.ollama_text_client import OllamaTextClient, OllamaTextClientError
from app.infrastructure.llm.ollama_vlm_client import OllamaVlmClient, OllamaVlmClientError

router = APIRouter(prefix="/api/extract", tags=["Extraction"])


class ExtractionResponseDTO(BaseModel):
    status: Literal["ok"]
    belge_tipi: BelgeTipi
    idempotency_key: str | None = None
    model: str
    taslak: IrsaliyeTaslagiSchema


_IDEMPOTENCY_CACHE: dict[str, ExtractionResponseDTO] = {}


def get_hibrit_extract_uc(settings: Settings = Depends(get_settings)) -> HibritExtractUseCase:
    text_llm_client = OllamaTextClient(settings)
    text_extractor = TextPdfExtractor(text_llm_client)
    vlm_llm_client = OllamaVlmClient(settings)
    vlm_extractor = VlmExtractor(vlm_llm_client, ImageRenderer())
    detector = BelgeTipiDedektoru()
    return HibritExtractUseCase(
        max_file_size_mb=settings.max_file_size_mb,
        detector=detector,
        text_extractor=text_extractor,
        vlm_extractor=vlm_extractor,
    )


get_text_pdf_extract_uc = get_hibrit_extract_uc


@router.post("/irsaliye", response_model=ExtractionResponseDTO)
async def extract_irsaliye(
    file: UploadFile = File(...),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    uc: HibritExtractUseCase = Depends(get_text_pdf_extract_uc),
) -> ExtractionResponseDTO:
    if idempotency_key and idempotency_key in _IDEMPOTENCY_CACHE:
        return _IDEMPOTENCY_CACHE[idempotency_key]

    content = await file.read()
    try:
        result = await uc.execute(
            filename=file.filename or "upload.pdf",
            content_type=file.content_type,
            content=content,
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except BelgeTipiAlgilamaError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OllamaTextClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except OllamaVlmClientError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except TextPdfExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ImageRenderingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except VlmExtractionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    response = ExtractionResponseDTO(
        status="ok",
        belge_tipi=result.belge_tipi,
        idempotency_key=idempotency_key,
        model=result.model,
        taslak=result.taslak,
    )
    if idempotency_key:
        _IDEMPOTENCY_CACHE[idempotency_key] = response
    return response
