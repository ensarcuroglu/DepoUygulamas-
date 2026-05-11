"""Health endpoint for DocAiService."""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings

router = APIRouter(tags=["Sistem"])


async def _fetch_ollama_tags(settings: Settings) -> dict:
    url = settings.ollama_base_url.rstrip("/") + "/api/tags"
    async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()


def _model_names(payload: dict) -> set[str]:
    models = payload.get("models", [])
    names: set[str] = set()
    if not isinstance(models, list):
        return names

    for item in models:
        if isinstance(item, str):
            names.add(item)
            continue
        if not isinstance(item, dict):
            continue
        for key in ("name", "model"):
            value = item.get(key)
            if isinstance(value, str) and value:
                names.add(value)
    return names


@router.get("/healthz")
async def healthz(settings: Settings = Depends(get_settings)) -> dict:
    try:
        tags_payload = await _fetch_ollama_tags(settings)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama baglantisi basarisiz",
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama tags endpoint hata dondu: {exc.response.status_code}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama tags yaniti JSON degil",
        ) from exc

    names = _model_names(tags_payload)
    if settings.ollama_text_model not in names:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Ollama text model bulunamadi: {settings.ollama_text_model}",
        )

    return {
        "status": "ok",
        "service": "DocAiService",
        "version": "0.1.0",
        "ollama": {
            "base_url": settings.ollama_base_url,
            "text_model": settings.ollama_text_model,
            "vlm_model": settings.ollama_vlm_model,
            "text_model_available": True,
        },
    }
