"""ExcelLoader limit + format davranisi."""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.infrastructure.parsing.excel_loader import (
    CorruptWorkbookError,
    EmptyWorkbookError,
    ExcelLoader,
    FileTooLargeError,
    TooManyRowsError,
    TooManySheetsError,
    UnsupportedFileFormatError,
)
from tests.conftest import make_rows, make_xlsx_bytes

pytestmark = pytest.mark.unit


def _loader() -> ExcelLoader:
    return ExcelLoader(get_settings())


def test_load_simple_xlsx_returns_workbook(simple_xlsx_bytes):
    workbook = _loader().load(filename="siparis.xlsx", content=simple_xlsx_bytes)
    assert workbook.filename == "siparis.xlsx"
    assert len(workbook.file_hash) == 64  # sha256 hex
    assert len(workbook.sheets) == 1
    sheet = workbook.primary_sheet
    assert sheet.name == "Sheet1"
    assert sheet.rows == 3
    assert sheet.columns == ["urun_kodu", "miktar", "birim_fiyat"]


def test_load_csv(csv_bytes):
    workbook = _loader().load(filename="siparis.csv", content=csv_bytes)
    sheet = workbook.primary_sheet
    assert sheet.name == "Sheet1"
    assert sheet.columns == ["urun_kodu", "miktar"]
    assert sheet.rows == 2


def test_load_unsupported_extension_raises():
    with pytest.raises(UnsupportedFileFormatError):
        _loader().load(filename="rapor.pdf", content=b"%PDF-1.4")


def test_load_empty_content_raises():
    with pytest.raises(EmptyWorkbookError):
        _loader().load(filename="bos.xlsx", content=b"")


def test_load_corrupt_xlsx_raises():
    with pytest.raises(CorruptWorkbookError):
        _loader().load(filename="kotu.xlsx", content=b"not-a-real-xlsx")


def test_load_too_many_rows_raises():
    # conftest MAX_ROWS=100
    big = make_xlsx_bytes({"Sheet1": make_rows(150)})
    with pytest.raises(TooManyRowsError):
        _loader().load(filename="buyuk.xlsx", content=big)


def test_load_too_many_sheets_raises():
    # conftest MAX_SHEETS=3
    sheets = {f"S{i}": [["a"], [1]] for i in range(5)}
    too_many = make_xlsx_bytes(sheets)
    with pytest.raises(TooManySheetsError):
        _loader().load(filename="cok.xlsx", content=too_many)


def test_load_file_too_large_raises():
    # conftest MAX_FILE_SIZE_MB=1
    big_content = b"x" * (2 * 1024 * 1024)  # 2 MB raw bytes
    with pytest.raises(FileTooLargeError):
        _loader().load(filename="dev.xlsx", content=big_content)


def test_load_normalizes_int_columns(simple_xlsx_bytes):
    # If headers come as int from pandas, loader stringifies them.
    rows = [[1, 2, 3], [10, 20, 30]]
    content = make_xlsx_bytes({"Sheet1": rows})
    workbook = _loader().load(filename="int_headers.xlsx", content=content)
    assert all(isinstance(c, str) for c in workbook.primary_sheet.columns)


def test_same_content_same_hash(simple_xlsx_bytes):
    """Hash content-based: ayni dosya = ayni hash."""
    a = _loader().load(filename="a.xlsx", content=simple_xlsx_bytes)
    b = _loader().load(filename="b.xlsx", content=simple_xlsx_bytes)
    assert a.file_hash == b.file_hash
