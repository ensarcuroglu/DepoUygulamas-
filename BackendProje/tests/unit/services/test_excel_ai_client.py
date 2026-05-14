"""ExcelAiClient unit testleri.

httpx isteklerini MockTransport ile yakalar; HTTP gercek olarak
yapilmaz. Header'lar (INTERNAL_API_KEY, Idempotency-Key), URL ve
multipart payload dogrulanir.
"""

from __future__ import annotations

from types import SimpleNamespace

import httpx
import pytest

from app.infrastructure.services.excel_ai_client import (
    ExcelAiClient,
    ExcelAiClientUnavailableError,
    ExcelAiClientUpstreamError,
)

pytestmark = pytest.mark.unit


def _settings(**overrides):
    """Minimal stub — ExcelAiClient yalnizca uc alan okur."""
    base = dict(
        excel_ai_service_url="http://excel-ai.test",
        excel_ai_service_timeout=5.0,
        internal_api_key="unit-test-key",
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _patch_transport(monkeypatch, handler):
    """httpx.Client'i kendi transport'umuza yonlendir."""
    transport = httpx.MockTransport(handler)
    original_init = httpx.Client.__init__

    def patched_init(self, *args, **kwargs):
        kwargs["transport"] = transport
        original_init(self, *args, **kwargs)

    monkeypatch.setattr(httpx.Client, "__init__", patched_init)


def test_hedef_semalar_sends_api_key_and_returns_dict(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"schemas": [{"name": "urun"}]})

    _patch_transport(monkeypatch, handler)
    client = ExcelAiClient(_settings())

    result = client.hedef_semalar()

    assert result == {"schemas": [{"name": "urun"}]}
    assert captured["url"] == "http://excel-ai.test/api/excel/hedef-semalar"
    assert captured["headers"]["x-internal-api-key"] == "unit-test-key"


def test_yorumla_forwards_multipart_and_idempotency_header(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        captured["url"] = str(request.url)
        captured["content_type"] = request.headers.get("content-type", "")
        captured["body"] = request.read()
        return httpx.Response(
            200,
            json={"workbook": {"filename": "x.xlsx"}, "answer": "tamam"},
        )

    _patch_transport(monkeypatch, handler)
    client = ExcelAiClient(_settings())

    result = client.yorumla(
        filename="x.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        content=b"binary-xlsx-content",
        soru="kac satir?",
        sheet_name="Sayfa1",
        idempotency_key="abc:yorumla:def",
    )

    assert result["answer"] == "tamam"
    assert captured["url"] == "http://excel-ai.test/api/excel/yorumla"
    assert captured["headers"]["x-internal-api-key"] == "unit-test-key"
    assert captured["headers"]["idempotency-key"] == "abc:yorumla:def"
    assert "multipart/form-data" in captured["content_type"]
    body = captured["body"]
    assert b"binary-xlsx-content" in body
    assert b"kac satir?" in body
    assert b"Sayfa1" in body


def test_sema_esle_forwards_hedef_sema(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = request.read()
        return httpx.Response(200, json={"target_schema": "siparis_kalemleri"})

    _patch_transport(monkeypatch, handler)
    client = ExcelAiClient(_settings())

    result = client.sema_esle(
        filename="a.xlsx",
        content_type=None,
        content=b"xlsx",
        hedef_sema="siparis_kalemleri",
    )

    assert result["target_schema"] == "siparis_kalemleri"
    assert captured["url"] == "http://excel-ai.test/api/excel/sema-esle"
    assert b"siparis_kalemleri" in captured["body"]


def test_missing_internal_key_raises_503(monkeypatch):
    client = ExcelAiClient(_settings(internal_api_key=None))
    with pytest.raises(ExcelAiClientUnavailableError) as ei:
        client.hedef_semalar()
    assert ei.value.status_code == 503


def test_upstream_error_propagates_status_and_detail(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "gecersiz sema"})

    _patch_transport(monkeypatch, handler)
    client = ExcelAiClient(_settings())

    with pytest.raises(ExcelAiClientUpstreamError) as ei:
        client.sema_esle(
            filename="a.xlsx",
            content_type=None,
            content=b"x",
            hedef_sema="yok",
        )
    assert ei.value.status_code == 422
    assert "gecersiz sema" in ei.value.message


def test_invalid_json_response_raises(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not-json")

    _patch_transport(monkeypatch, handler)
    client = ExcelAiClient(_settings())

    with pytest.raises(Exception):
        client.hedef_semalar()
