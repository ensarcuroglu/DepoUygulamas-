"""ExcelSemaEsleUseCase: dosya + hedef sema -> sutun esleme onerisi."""

from __future__ import annotations

import hashlib
import logging

from app.core.entities.responses import (
    ExcelSemaEsleOutput,
    SheetInfo,
    WorkbookInfo,
)
from app.core.entities.wms_target_schemas import get_target_schema
from app.core.services.sema_matcher import match_columns
from app.infrastructure.observability.langfuse_tracing import safe_metadata, trace_span
from app.infrastructure.parsing.excel_loader import ExcelLoader, LoadedWorkbook

log = logging.getLogger(__name__)


class ExcelSemaEsleUseCase:
    """Sutun esleme onerisi: deterministik, LLM cagrisi yok."""

    def __init__(self, *, loader: ExcelLoader) -> None:
        self._loader = loader

    def execute(
        self,
        *,
        filename: str,
        content: bytes,
        target_schema: str,
        sheet_name: str | None = None,
    ) -> ExcelSemaEsleOutput:
        schema = get_target_schema(target_schema)
        workbook = self._loader.load(filename=filename, content=content)
        sheet = _pick_sheet(workbook, sheet_name)

        with trace_span(
            "excel-ai.sema-esle",
            input_data={
                "filename": workbook.filename,
                "sheet": sheet.name,
                "target_schema": schema.name,
                "rows": sheet.rows,
                "columns": sheet.columns,
                "size_bytes": workbook.size_bytes,
            },
            metadata=safe_metadata(
                endpoint="/api/excel/sema-esle",
                operation="schema_match",
                file_hash=workbook.file_hash,
                target_schema=schema.name,
                sheet=sheet.name,
                rows=sheet.rows,
                column_count=len(sheet.columns),
            ),
            tags=["excel", "schema-match"],
        ) as span:
            mappings = match_columns(
                source_columns=sheet.columns,
                schema=schema,
            )

            matched = sorted({m.target_field for m in mappings if m.target_field})
            unmatched_sources = [m.source_column for m in mappings if m.target_field is None]
            missing_required = sorted(
                f for f in schema.required_field_names if f not in matched
            )
            span.update(
                output={
                    "matched_count": len(matched),
                    "missing_required_count": len(missing_required),
                    "unmatched_source_count": len(unmatched_sources),
                },
                metadata=safe_metadata(status="ok"),
            )

        idem = _idempotency_key(
            file_hash=workbook.file_hash,
            operation="sema-esle",
            params={"sheet": sheet.name, "target": target_schema},
        )

        log.info(
            "ExcelSemaEsle: file=%s sheet=%s target=%s matched=%d missing_required=%d",
            filename,
            sheet.name,
            target_schema,
            len(matched),
            len(missing_required),
        )

        return ExcelSemaEsleOutput(
            workbook=WorkbookInfo(
                filename=workbook.filename,
                file_hash=workbook.file_hash,
                size_bytes=workbook.size_bytes,
                sheets=[
                    SheetInfo(name=s.name, rows=s.rows, columns=s.columns)
                    for s in workbook.sheets
                ],
            ),
            sheet_name=sheet.name,
            target_schema=schema.name,
            mappings=mappings,
            matched_target_fields=matched,
            missing_required_fields=missing_required,
            unmatched_source_columns=unmatched_sources,
            idempotency_key=idem,
        )


def _pick_sheet(workbook: LoadedWorkbook, sheet_name: str | None):
    if sheet_name is None:
        return workbook.primary_sheet
    for sheet in workbook.sheets:
        if sheet.name == sheet_name:
            return sheet
    raise ValueError(
        f"Sayfa bulunamadi: '{sheet_name}'. Mevcut: {[s.name for s in workbook.sheets]}"
    )


def _idempotency_key(*, file_hash: str, operation: str, params: dict) -> str:
    canonical = "|".join(f"{k}={params[k]}" for k in sorted(params))
    params_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{file_hash}:{operation}:{params_hash}"
