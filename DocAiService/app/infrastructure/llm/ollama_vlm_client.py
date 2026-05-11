"""Ollama multimodal/VLM client."""

from __future__ import annotations

import httpx

from app.core.config import Settings
from app.infrastructure.llm.ollama_text_client import _parse_json_content


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

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.RequestError as exc:
            raise OllamaVlmClientError("Ollama VLM baglantisi basarisiz") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaVlmClientError(
                f"Ollama VLM hata dondu: {exc.response.status_code}"
            ) from exc
        except ValueError as exc:
            raise OllamaVlmClientError("Ollama VLM JSON olmayan yanit verdi") from exc

        content = body.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise OllamaVlmClientError("Ollama VLM bos icerik dondurdu")
        try:
            return _parse_json_content(content)
        except RuntimeError as exc:
            raise OllamaVlmClientError(str(exc)) from exc
