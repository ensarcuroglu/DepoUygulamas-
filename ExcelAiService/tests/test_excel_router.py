"""Excel router happy-path + auth + cache + hata haritasi."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.v1.routers import excel as excel_module
from app.application.agents.pandas_qa_agent import AgentAnswer
from main import app
from tests.conftest import TEST_KEY, make_xlsx_bytes


@pytest.fixture(autouse=True)
def _reset_cache():
    """Modul seviye singleton cache'i her test arasinda temizle."""
    if excel_module._CACHE is not None:
        excel_module._CACHE.clear()
    excel_module._CACHE = None
    yield
    if excel_module._CACHE is not None:
        excel_module._CACHE.clear()


@pytest.fixture
def patch_agent(monkeypatch: pytest.MonkeyPatch):
    """PandasQaAgent.ask'i deterministik mock cevap ile degistir."""
    def fake_ask(self, df, question):
        return AgentAnswer(answer=f"cevap: {question}", raw_output=f"cevap: {question}")

    monkeypatch.setattr(
        "app.application.agents.pandas_qa_agent.PandasQaAgent.ask",
        fake_ask,
    )


def _headers() -> dict[str, str]:
    return {"X-Internal-Api-Key": TEST_KEY}


# ──────────────────────────── AUTH ────────────────────────────


def test_yorumla_missing_api_key_returns_503(simple_xlsx_bytes):
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
        )
    assert r.status_code == 503


def test_yorumla_wrong_api_key_returns_503(simple_xlsx_bytes):
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            headers={"X-Internal-Api-Key": "yanlis"},
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
        )
    assert r.status_code == 503


# ─────────────────────────── YORUMLA ───────────────────────────


def test_yorumla_without_question_returns_summary_only(simple_xlsx_bytes):
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            headers=_headers(),
            files={"file": ("siparis.xlsx", simple_xlsx_bytes)},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["question"] is None
    assert body["answer"] is None
    assert body["sheet_name"] == "Sheet1"
    assert body["summary"]["rows"] == 3
    assert body["summary"]["columns"] == ["urun_kodu", "miktar", "birim_fiyat"]
    assert body["workbook"]["filename"] == "siparis.xlsx"
    assert len(body["workbook"]["file_hash"]) == 64
    assert body["idempotency_key"].startswith(body["workbook"]["file_hash"])


def test_yorumla_with_question_calls_agent(simple_xlsx_bytes, patch_agent):
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            headers=_headers(),
            files={"file": ("siparis.xlsx", simple_xlsx_bytes)},
            data={"soru": "kac satir var?"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["question"] == "kac satir var?"
    assert body["answer"] == "cevap: kac satir var?"


def test_yorumla_idempotency_cache_returns_same_payload(
    simple_xlsx_bytes, patch_agent
):
    with TestClient(app) as client:
        r1 = client.post(
            "/api/excel/yorumla",
            headers={**_headers(), "Idempotency-Key": "demo-1"},
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
            data={"soru": "ortalama nedir?"},
        )
        r2 = client.post(
            "/api/excel/yorumla",
            headers={**_headers(), "Idempotency-Key": "demo-1"},
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
            data={"soru": "ortalama nedir?"},
        )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


def test_yorumla_unsupported_format_returns_422():
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            headers=_headers(),
            files={"file": ("doc.pdf", b"%PDF-1.4")},
        )
    assert r.status_code == 422


def test_yorumla_file_too_large_returns_413():
    # conftest MAX_FILE_SIZE_MB=1
    big = b"x" * (2 * 1024 * 1024)
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            headers=_headers(),
            files={"file": ("buyuk.xlsx", big)},
        )
    assert r.status_code == 413


# ─────────────────────────── SEMA-ESLE ───────────────────────────


def test_sema_esle_happy_path_siparis_kalemleri(simple_xlsx_bytes):
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/sema-esle",
            headers=_headers(),
            files={"file": ("siparis.xlsx", simple_xlsx_bytes)},
            data={"hedef_sema": "siparis_kalemleri"},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["target_schema"] == "siparis_kalemleri"
    assert "urun_kodu" in body["matched_target_fields"]
    assert "miktar" in body["matched_target_fields"]
    # siparis_no zorunlu ama dosyada yok
    assert "siparis_no" in body["missing_required_fields"]


def test_sema_esle_invalid_schema_returns_422(simple_xlsx_bytes):
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/sema-esle",
            headers=_headers(),
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
            data={"hedef_sema": "yok_boyle_sema"},
        )
    assert r.status_code == 422


def test_sema_esle_deterministic_same_file_same_output(simple_xlsx_bytes):
    with TestClient(app) as client:
        r1 = client.post(
            "/api/excel/sema-esle",
            headers=_headers(),
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
            data={"hedef_sema": "siparis_kalemleri"},
        )
        r2 = client.post(
            "/api/excel/sema-esle",
            headers=_headers(),
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
            data={"hedef_sema": "siparis_kalemleri"},
        )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()


# ─────────────────────────── HEDEF SEMALAR ───────────────────────────


def test_hedef_semalar_lists_three_schemas():
    with TestClient(app) as client:
        r = client.get("/api/excel/hedef-semalar", headers=_headers())
    assert r.status_code == 200
    names = [s["name"] for s in r.json()["schemas"]]
    assert set(names) == {"siparis_kalemleri", "stok_sayim_kalemleri", "urun"}


# ─────────────────────────── MULTI-SHEET ───────────────────────────


def test_yorumla_with_sheet_selection():
    content = make_xlsx_bytes(
        {
            "Sayfa1": [["a", "b"], [1, 2]],
            "Sayfa2": [["x", "y"], [10, 20], [30, 40]],
        }
    )
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            headers=_headers(),
            files={"file": ("multi.xlsx", content)},
            data={"sheet_name": "Sayfa2"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["sheet_name"] == "Sayfa2"
    assert body["summary"]["rows"] == 2  # Sayfa2 = 2 veri satiri


def test_yorumla_invalid_sheet_returns_422(simple_xlsx_bytes):
    with TestClient(app) as client:
        r = client.post(
            "/api/excel/yorumla",
            headers=_headers(),
            files={"file": ("a.xlsx", simple_xlsx_bytes)},
            data={"sheet_name": "Olmayan"},
        )
    assert r.status_code == 422
