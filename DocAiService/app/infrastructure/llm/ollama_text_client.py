"""Ollama text LLM client."""

from __future__ import annotations

import json
import time

import httpx

from app.core.config import Settings
from app.infrastructure.observability.langfuse_tracing import (
    safe_metadata,
    summarize_text,
    trace_generation,
)


class OllamaTextClientError(RuntimeError):
    """Raised when Ollama cannot return a valid JSON response."""


class OllamaTextClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_text_model
        self.timeout = settings.llm_timeout

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict:
        started = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        }

        with trace_generation(
            "doc-ai.ollama-text",
            model=self.model,
            input_data={
                "system_prompt": summarize_text(system_prompt),
                "user_prompt": summarize_text(user_prompt),
            },
            metadata=safe_metadata(
                operation="text_pdf_extraction",
                ollama_base_url=self.base_url,
                timeout=self.timeout,
            ),
            tags=["doc", "text"],
        ) as observation:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(f"{self.base_url}/api/chat", json=payload)
                    response.raise_for_status()
                    body = response.json()
            except httpx.RequestError as exc:
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type=type(exc).__name__,
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise OllamaTextClientError("Ollama text LLM baglantisi basarisiz") from exc
            except httpx.HTTPStatusError as exc:
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type=type(exc).__name__,
                        status_code=exc.response.status_code,
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise OllamaTextClientError(
                    f"Ollama text LLM hata dondu: {exc.response.status_code}"
                ) from exc
            except ValueError as exc:
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type=type(exc).__name__,
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise OllamaTextClientError("Ollama text LLM JSON olmayan yanit verdi") from exc

            content = body.get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type="EmptyContent",
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise OllamaTextClientError("Ollama text LLM bos icerik dondurdu")
            try:
                parsed = _parse_json_content(content)
            except RuntimeError as exc:
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type=type(exc).__name__,
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise
            observation.update(
                output={
                    "content": summarize_text(content),
                    "json_keys": sorted(parsed.keys()),
                },
                metadata=safe_metadata(
                    status="ok",
                    latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    response_keys=sorted(body.keys()),
                ),
            )
            return parsed


def _parse_json_content(content: str) -> dict:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").strip()
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise OllamaTextClientError("LLM yanitinda JSON nesnesi bulunamadi") from None
        try:
            parsed = json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError as exc:
            raise OllamaTextClientError("LLM yaniti gecerli JSON degil") from exc

    if not isinstance(parsed, dict):
        raise OllamaTextClientError("LLM JSON yaniti nesne degil")
    return parsed
