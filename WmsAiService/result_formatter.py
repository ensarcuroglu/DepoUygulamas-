"""
SQL execute sonucunu yapılandırılmış formata çevirir.

`SQLDatabase.run` çıktısı string olduğu için qwen2.5-coder:7b yorumlamakta zorlanıyor.
Bu modül SQLAlchemy üzerinden ham `RowMapping` listesi alır, kolon adlı
dict satırlara dönüştürür ve cevap üretimi için intent tespiti yapar.

Tasarım kararları:
- `intent` enumeration üç ana sınıfa ayırır: SCALAR / EMPTY / LIST.
- SCALAR: tek satır + tek kolon, sayısal ya da metin tek değer.
  -> Cevap LLM'siz, deterministik şablonla üretilir.
- EMPTY: 0 satır.
  -> Sabit Türkçe cümle.
- LIST: çok satır veya çok kolon.
  -> Cevap LLM ile (few-shot ile disipline edilir, prompt'u kısa tutmak için
     ilk N satır verilir).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

DEFAULT_LIST_PREVIEW_ROWS = 15


class ResultIntent(str, Enum):
    SCALAR = "scalar"
    EMPTY = "empty"
    LIST = "list"
    DOC_ANSWER = "doc_answer"


@dataclass
class StructuredResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    intent: ResultIntent
    # Yalnızca SCALAR'da set edilir
    scalar_value: Any | None = None
    scalar_column: str | None = None


def execute_structured(engine: Engine, sql: str) -> StructuredResult:
    """SQL'i çalıştırıp yapılandırılmış sonuç döndürür."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(row) for row in result.mappings().all()]

    row_count = len(rows)
    intent = _classify(columns, rows)

    scalar_value = None
    scalar_column = None
    if intent == ResultIntent.SCALAR:
        scalar_column = columns[0]
        scalar_value = rows[0][scalar_column]

    return StructuredResult(
        columns=columns,
        rows=rows,
        row_count=row_count,
        intent=intent,
        scalar_value=scalar_value,
        scalar_column=scalar_column,
    )


def _classify(columns: list[str], rows: list[dict[str, Any]]) -> ResultIntent:
    if not rows:
        return ResultIntent.EMPTY
    if len(rows) == 1 and len(columns) == 1:
        return ResultIntent.SCALAR
    return ResultIntent.LIST


def render_rows_for_prompt(
    rows: list[dict[str, Any]],
    limit: int = DEFAULT_LIST_PREVIEW_ROWS,
) -> str:
    """LLM cevap promptuna gömmek için kompakt, etiketli satır gösterimi.

    JSON yerine `key: value` formatı küçük modellerde daha az tokenize
    karışıklığı yaratır ve kolon adlarını okunabilir tutar.
    """
    if not rows:
        return "(boş sonuç)"
    preview = rows[:limit]
    blocks: list[str] = []
    for i, row in enumerate(preview, 1):
        pairs = ", ".join(f"{k}={_fmt(v)}" for k, v in row.items())
        blocks.append(f"{i}) {pairs}")
    suffix = ""
    if len(rows) > limit:
        suffix = f"\n... ({len(rows) - limit} satır daha var)"
    return "\n".join(blocks) + suffix


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        # Gereksiz ondalık basamakları temizle
        if value == int(value):
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def render_doc_answer(answer: str, sources: list[dict[str, Any]]) -> str:
    """Render a RAG answer as Markdown with optional source bullets."""
    cleaned = answer.strip()
    if not cleaned or not sources:
        return cleaned

    source_lines: list[str] = []
    for source in sources[:5]:
        path = source.get("source_path") or "bilinmeyen kaynak"
        section = source.get("section")
        label = f"`{path}`"
        if section:
            label += f" - {section}"
        source_lines.append(f"- {label}")

    if not source_lines:
        return cleaned
    return f"{cleaned}\n\n**Kaynaklar**\n" + "\n".join(source_lines)
