"""Use case cevaplari icin framework-agnostic dataclass'lar.

Bu modul Pydantic'e bagimli degildir; router katmani gerekirse
bu dataclass'lari kendi response_model'ine cevirir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class SheetInfo:
    name: str
    rows: int
    columns: list[str]


@dataclass(frozen=True)
class WorkbookInfo:
    filename: str
    file_hash: str
    size_bytes: int
    sheets: list[SheetInfo]


@dataclass(frozen=True)
class DataFrameSummaryDTO:
    rows: int
    columns: list[str]
    dtypes: dict[str, str]
    head: list[dict[str, Any]]
    describe: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class ExcelYorumlaOutput:
    workbook: WorkbookInfo
    sheet_name: str
    summary: DataFrameSummaryDTO
    question: str | None
    answer: str | None
    idempotency_key: str


@dataclass(frozen=True)
class FieldMatchCandidate:
    target_field: str
    score: float


@dataclass(frozen=True)
class ColumnMapping:
    source_column: str
    target_field: str | None
    confidence: float
    candidates: list[FieldMatchCandidate] = field(default_factory=list)


@dataclass(frozen=True)
class ExcelSemaEsleOutput:
    workbook: WorkbookInfo
    sheet_name: str
    target_schema: str
    mappings: list[ColumnMapping]
    matched_target_fields: list[str]
    missing_required_fields: list[str]
    unmatched_source_columns: list[str]
    idempotency_key: str
