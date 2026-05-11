"""VLM extraction and Ollama multimodal client tests."""

from __future__ import annotations

import asyncio

import pytest

from app.core.config import get_settings, load_settings
from app.core.entities.belge import Belge, BelgeTipi
from app.infrastructure.extraction.image_renderer import RenderedImage
from app.infrastructure.extraction.vlm_extractor import VlmExtractor
from app.infrastructure.llm.ollama_vlm_client import OllamaVlmClient


def sample_payload() -> dict:
    return {
        "tedarikci": {"value": "ACME GIDA A.S.", "confidence": 0.86},
        "irsaliye_no": {"value": "IMG-2026-1", "confidence": 0.78},
        "tarih": {"value": "2026-05-11", "confidence": 0.8},
        "kalemler": [
            {
                "urun_kodu": {"value": "URUN-001", "confidence": 0.74},
                "ad": {"value": "Pirinc", "confidence": 0.72},
                "miktar": {"value": 10, "confidence": 0.77},
                "birim": {"value": "KG", "confidence": 0.76},
            }
        ],
        "toplam": {"value": 10, "confidence": 0.7},
    }


@pytest.fixture(autouse=True)
def settings_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setenv("OLLAMA_VLM_MODEL", "qwen3-vl:4b")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.extraction
def test_vlm_extractor_maps_image_payload_to_schema():
    class FakeRenderer:
        def render(self, belge: Belge, belge_tipi: BelgeTipi) -> RenderedImage:
            assert belge_tipi is BelgeTipi.IMAGE
            return RenderedImage(
                image_base64="ZmFrZS1pbWFnZQ==",
                mime_type="image/jpeg",
                width=640,
                height=480,
            )

    class FakeVlmClient:
        model = "qwen3-vl:4b"

        async def chat_image_json(
            self,
            *,
            system_prompt: str,
            user_prompt: str,
            image_base64: str,
        ) -> dict:
            assert "JSON semasi" in system_prompt
            assert "gorsel" in user_prompt.lower()
            assert image_base64 == "ZmFrZS1pbWFnZQ=="
            return sample_payload()

    extractor = VlmExtractor(FakeVlmClient(), FakeRenderer())
    result = asyncio.run(
        extractor.extract(
            Belge(filename="irsaliye.jpg", content_type="image/jpeg", content=b"fake"),
            belge_tipi=BelgeTipi.IMAGE,
        )
    )

    assert result.belge_tipi is BelgeTipi.IMAGE
    assert result.model == "qwen3-vl:4b"
    assert result.taslak.confidence_score > 0.7
    assert result.metadata["image_width"] == 640


def test_ollama_vlm_client_uses_configurable_local_model():
    settings = load_settings(use_env_file=False)
    client = OllamaVlmClient(settings)

    assert client.model == "qwen3-vl:4b"


def test_ollama_vlm_client_sends_image_payload(monkeypatch: pytest.MonkeyPatch):
    captured: dict = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"message": {"content": '{"tedarikci":{"value":"A","confidence":0.8}}'}}

    class FakeAsyncClient:
        def __init__(self, *, timeout: float) -> None:
            captured["timeout"] = timeout

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(self, url: str, json: dict):
            captured["url"] = url
            captured["payload"] = json
            return FakeResponse()

    monkeypatch.setattr("httpx.AsyncClient", FakeAsyncClient)

    client = OllamaVlmClient(load_settings(use_env_file=False))
    parsed = asyncio.run(
        client.chat_image_json(
            system_prompt="system",
            user_prompt="user",
            image_base64="base64-image",
        )
    )

    assert parsed["tedarikci"]["value"] == "A"
    assert captured["url"] == "http://ollama.test/api/chat"
    assert captured["payload"]["model"] == "qwen3-vl:4b"
    assert captured["payload"]["messages"][1]["images"] == ["base64-image"]
