"""Excel/CSV dosyalarini pandas DataFrame'e ceviren yukleyici."""

from __future__ import annotations

import hashlib
import io
import logging
from dataclasses import dataclass
from pathlib import PurePath

import pandas as pd

from app.core.config import Settings

log = logging.getLogger(__name__)

_EXCEL_SUFFIXES = {".xlsx", ".xlsm"}
_CSV_SUFFIXES = {".csv", ".tsv"}
_SUPPORTED_SUFFIXES = _EXCEL_SUFFIXES | _CSV_SUFFIXES


class ExcelLoadError(Exception):
    """Excel/CSV yukleme sirasinda olusan hatalar icin base sinif."""


class UnsupportedFileFormatError(ExcelLoadError):
    pass


class FileTooLargeError(ExcelLoadError):
    pass


class TooManySheetsError(ExcelLoadError):
    pass


class TooManyRowsError(ExcelLoadError):
    pass


class EmptyWorkbookError(ExcelLoadError):
    pass


class CorruptWorkbookError(ExcelLoadError):
    pass


@dataclass(frozen=True)
class LoadedSheet:
    name: str
    rows: int
    columns: list[str]
    dataframe: pd.DataFrame


@dataclass(frozen=True)
class LoadedWorkbook:
    """Yuklenmis Excel/CSV dosyasinin in-memory temsili."""

    filename: str
    file_hash: str
    size_bytes: int
    sheets: list[LoadedSheet]

    @property
    def primary_sheet(self) -> LoadedSheet:
        return self.sheets[0]


class ExcelLoader:
    """Bytes -> LoadedWorkbook.

    Tum limit kontrolleri burada uygulanir; agent / use case katmani
    yalnizca dogrulanmis bir LoadedWorkbook alir.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def load(self, *, filename: str, content: bytes) -> LoadedWorkbook:
        suffix = PurePath(filename).suffix.lower()
        if suffix not in _SUPPORTED_SUFFIXES:
            raise UnsupportedFileFormatError(
                f"Desteklenmeyen dosya uzantisi: '{suffix or '(yok)'}'. "
                f"Kabul edilenler: {sorted(_SUPPORTED_SUFFIXES)}"
            )

        size_bytes = len(content)
        max_bytes = self._settings.max_file_size_bytes
        if size_bytes > max_bytes:
            raise FileTooLargeError(
                f"Dosya boyutu {size_bytes / 1024 / 1024:.2f} MB; "
                f"limit {self._settings.max_file_size_mb} MB."
            )
        if size_bytes == 0:
            raise EmptyWorkbookError("Dosya bos.")

        file_hash = hashlib.sha256(content).hexdigest()

        try:
            if suffix in _EXCEL_SUFFIXES:
                sheets = self._read_excel(content)
            else:
                sheets = self._read_csv(content, suffix=suffix)
        except ExcelLoadError:
            raise
        except Exception as exc:
            log.warning("Dosya okuma hatasi: %s", exc, exc_info=True)
            raise CorruptWorkbookError(
                f"Dosya icerigi okunamadi: {exc.__class__.__name__}"
            ) from exc

        if not sheets:
            raise EmptyWorkbookError("Dosyada okunabilen sayfa bulunamadi.")

        return LoadedWorkbook(
            filename=filename,
            file_hash=file_hash,
            size_bytes=size_bytes,
            sheets=sheets,
        )

    def _read_excel(self, content: bytes) -> list[LoadedSheet]:
        buffer = io.BytesIO(content)
        # sheet_name=None -> tum sayfalar dict[str, DataFrame].
        raw = pd.read_excel(buffer, sheet_name=None, engine="openpyxl")

        if not raw:
            raise EmptyWorkbookError("Excel dosyasinda hic sayfa yok.")

        if len(raw) > self._settings.max_sheets:
            raise TooManySheetsError(
                f"Sayfa sayisi {len(raw)}; limit {self._settings.max_sheets}."
            )

        sheets: list[LoadedSheet] = []
        for name, df in raw.items():
            sheets.append(self._build_sheet(name=str(name), dataframe=df))
        return sheets

    def _read_csv(self, content: bytes, *, suffix: str) -> list[LoadedSheet]:
        buffer = io.BytesIO(content)
        sep = "\t" if suffix == ".tsv" else None  # None -> python engine sniffer
        try:
            df = pd.read_csv(buffer, sep=sep, engine="python")
        except UnicodeDecodeError:
            buffer.seek(0)
            df = pd.read_csv(buffer, sep=sep, engine="python", encoding="latin-1")
        return [self._build_sheet(name="Sheet1", dataframe=df)]

    def _build_sheet(self, *, name: str, dataframe: pd.DataFrame) -> LoadedSheet:
        if len(dataframe) > self._settings.max_rows:
            raise TooManyRowsError(
                f"'{name}' sayfasi {len(dataframe)} satir iceriyor; "
                f"limit {self._settings.max_rows}."
            )

        # Sutun adlarini string'e normalize et (pandas bazen int dondurur).
        dataframe.columns = [str(c).strip() for c in dataframe.columns]
        columns = list(dataframe.columns)

        return LoadedSheet(
            name=name,
            rows=int(len(dataframe)),
            columns=columns,
            dataframe=dataframe,
        )
