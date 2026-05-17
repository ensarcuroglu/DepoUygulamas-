"""Ollama multimodal/VLM client."""

from __future__ import annotations

import time

import httpx

from app.core.config import Settings
from app.infrastructure.llm.ollama_text_client import _parse_json_content
from app.infrastructure.observability.langfuse_tracing import (
    safe_metadata,
    summarize_text,
    trace_generation,
)


class OllamaVlmClientError(RuntimeError):
    """Raised when Ollama VLM cannot return a valid JSON response."""


class OllamaVlmClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_vlm_model
        self.timeout = settings.llm_timeout

    async def chat_image_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_base64: str,
    ) -> dict:
        started = time.perf_counter()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": user_prompt,
                    "images": [image_base64],
                },
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        }

        with trace_generation(
            "doc-ai.ollama-vlm",
            model=self.model,
            input_data={
                "system_prompt": summarize_text(system_prompt),
                "user_prompt": summarize_text(user_prompt),
                "image": {"redacted": "base64", "chars": len(image_base64)},
            },
            metadata=safe_metadata(
                operation="visual_extraction",
                ollama_base_url=self.base_url,
                timeout=self.timeout,
            ),
            tags=["doc", "vlm"],
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
                raise OllamaVlmClientError("Ollama VLM baglantisi basarisiz") from exc
            except httpx.HTTPStatusError as exc:
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type=type(exc).__name__,
                        status_code=exc.response.status_code,
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise OllamaVlmClientError(
                    f"Ollama VLM hata dondu: {exc.response.status_code}"
                ) from exc
            except ValueError as exc:
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type=type(exc).__name__,
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise OllamaVlmClientError("Ollama VLM JSON olmayan yanit verdi") from exc

            content = body.get("message", {}).get("content")
            if not isinstance(content, str) or not content.strip():
                observation.update(
                    metadata=safe_metadata(
                        status="error",
                        error_type="EmptyContent",
                        latency_ms=round((time.perf_counter() - started) * 1000, 2),
                    )
                )
                raise OllamaVlmClientError("Ollama VLM bos icerik dondurdu")
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
                raise OllamaVlmClientError(str(exc)) from exc
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
