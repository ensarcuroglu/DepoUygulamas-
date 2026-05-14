"""Shared test fixtures for ExcelAiService."""

from __future__ import annotations

import io
from typing import Iterable

import openpyxl
import pytest

from app.core.config import get_settings

TEST_KEY = "test-internal-key"
TEST_MODEL = "qwen2.5-coder:7b"


@pytest.fixture(autouse=True)
def _isolate_settings(monkeypatch: pytest.MonkeyPatch):
    """Every test starts with a fresh, predictable Settings instance."""
    monkeypatch.setenv("EXCEL_AI_ENV_FILE", "__test_missing.env")
    monkeypatch.setenv("INTERNAL_API_KEY", TEST_KEY)
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.test")
    monkeypatch.setenv("OLLAMA_TEXT_MODEL", TEST_MODEL)
    monkeypatch.setenv("MAX_FILE_SIZE_MB", "1")
    monkeypatch.setenv("MAX_ROWS", "100")
    monkeypatch.setenv("MAX_SHEETS", "3")
    monkeypatch.setenv("IDEMPOTENCY_TTL_SECONDS", "60")
    monkeypatch.setenv("IDEMPOTENCY_MAX_ENTRIES", "16")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def make_xlsx_bytes(
    sheets: dict[str, list[list]] | None = None,
) -> bytes:
    """Create an in-memory XLSX file from a dict of sheet_name -> rows."""
    sheets = sheets or {
        "Sheet1": [
            ["urun_kodu", "miktar", "birim_fiyat"],
            ["SKU-1", 10, 2.50],
            ["SKU-2", 5, 7.10],
            ["SKU-3", 12, 1.25],
        ],
    }
    wb = openpyxl.Workbook()
    # Replace default sheet
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(title=name)
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.fixture
def simple_xlsx_bytes() -> bytes:
    return make_xlsx_bytes()


@pytest.fixture
def csv_bytes() -> bytes:
    return b"urun_kodu,miktar\nSKU-1,3\nSKU-2,7\n"


def make_rows(n_rows: int, headers: Iterable[str] = ("a", "b")) -> list[list]:
    rows: list[list] = [list(headers)]
    for i in range(n_rows):
        rows.append([f"v{i}", i])
    return rows
