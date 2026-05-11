"""Ollama text LLM client."""

from __future__ import annotations

import json

import httpx

from app.core.config import Settings


class OllamaTextClientError(RuntimeError):
    """Raised when Ollama cannot return a valid JSON response."""


class OllamaTextClient:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_text_model
        self.timeout = settings.llm_timeout

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict:
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

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                body = response.json()
        except httpx.RequestError as exc:
            raise OllamaTextClientError("Ollama text LLM baglantisi basarisiz") from exc
        except httpx.HTTPStatusError as exc:
            raise OllamaTextClientError(
                f"Ollama text LLM hata dondu: {exc.response.status_code}"
            ) from exc
        except ValueError as exc:
            raise OllamaTextClientError("Ollama text LLM JSON olmayan yanit verdi") from exc

        content = body.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise OllamaTextClientError("Ollama text LLM bos icerik dondurdu")
        return _parse_json_content(content)


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
