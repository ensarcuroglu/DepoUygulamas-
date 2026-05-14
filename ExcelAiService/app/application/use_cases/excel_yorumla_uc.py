"""ExcelYorumlaUseCase: dosya + (opsiyonel) soru -> ozet + cevap."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import asdict

from app.application.agents.pandas_qa_agent import (
    PandasQaAgent,
    summarize_dataframe,
)
from app.core.entities.responses import (
    DataFrameSummaryDTO,
    ExcelYorumlaOutput,
    SheetInfo,
    WorkbookInfo,
)
from app.infrastructure.parsing.excel_loader import ExcelLoader, LoadedWorkbook

log = logging.getLogger(__name__)


class ExcelYorumlaUseCase:
    """Excel yorumlama akisinin orchestration noktasi.

    LLM cagrisi yalnizca ``question`` saglandiginda yapilir; aksi halde
    deterministik ``summarize_dataframe`` cevabi doner.
    """

    def __init__(
        self,
        *,
        loader: ExcelLoader,
        agent: PandasQaAgent | None,
    ) -> None:
        self._loader = loader
        self._agent = agent

    def execute(
        self,
        *,
        filename: str,
        content: bytes,
        question: str | None,
        sheet_name: str | None = None,
    ) -> ExcelYorumlaOutput:
        workbook = self._loader.load(filename=filename, content=content)
        sheet = _pick_sheet(workbook, sheet_name)
        summary = summarize_dataframe(sheet.dataframe)

        answer: str | None = None
        normalized_q = (question or "").strip() or None
        if normalized_q:
            if self._agent is None:
                raise RuntimeError(
                    "Soru ile cagrildi ancak agent yapilandirilmamis. "
                    "Ollama erisimini ve PandasQaAgent DI'sini kontrol edin."
                )
            agent_result = self._agent.ask(sheet.dataframe, normalized_q)
            answer = agent_result.answer

        idem = _idempotency_key(
            file_hash=workbook.file_hash,
            operation="yorumla",
            params={"sheet": sheet.name, "question": normalized_q or ""},
        )

        log.info(
            "ExcelYorumla: file=%s sheet=%s rows=%s soru=%s",
            filename,
            sheet.name,
            sheet.rows,
            bool(normalized_q),
        )

        return ExcelYorumlaOutput(
            workbook=_workbook_info(workbook),
            sheet_name=sheet.name,
            summary=DataFrameSummaryDTO(**asdict(summary)),
            question=normalized_q,
            answer=answer,
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


def _workbook_info(workbook: LoadedWorkbook) -> WorkbookInfo:
    return WorkbookInfo(
        filename=workbook.filename,
        file_hash=workbook.file_hash,
        size_bytes=workbook.size_bytes,
        sheets=[
            SheetInfo(name=s.name, rows=s.rows, columns=s.columns)
            for s in workbook.sheets
        ],
    )


def _idempotency_key(*, file_hash: str, operation: str, params: dict) -> str:
    """`sha256(file):<operation>:sha256(params)` formati."""
    canonical = "|".join(f"{k}={params[k]}" for k in sorted(params))
    params_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{file_hash}:{operation}:{params_hash}"
