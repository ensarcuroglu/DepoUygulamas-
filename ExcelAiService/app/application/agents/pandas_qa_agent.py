"""LangChain pandas DataFrame agent + template-first ozet.

Iki yol sunulur:

1. ``summarize_dataframe(df)``: deterministik, LLM'siz hizli ozet
   (`describe`, dtypes, head ornegi). Use case bunu her zaman uretir
   ve yaniti zenginlestirir.

2. ``PandasQaAgent.ask(df, question)``: LangChain
   ``create_pandas_dataframe_agent`` + Ollama LLM. Pandas DataFrame
   agent'i ``PythonAstREPLTool`` kullandigi icin LangChain
   ``allow_dangerous_code=True`` opt-in'ini zorunlu kilar.

Guvenlik notu: Agent yalnizca `INTERNAL_API_KEY` ile authenticate
edilmis dahili istemcilere acik bir mikroservis icinde calisir.
Yine de input dosya boyutu/satir limitleri (`ExcelLoader`) ve
``max_iterations`` ile kacis senaryolari sinirlanir.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
from langchain_core.language_models import BaseLanguageModel
from langchain_experimental.agents.agent_toolkits import create_pandas_dataframe_agent

log = logging.getLogger(__name__)


_AGENT_PREFIX_TR = """Sen, Turkce konusan bir veri analiz asistanisin.
Sana verilen pandas DataFrame uzerinde sorulari yanitla.

Kurallar:
- Yalnizca verilen DataFrame uzerinde calis; baska bir dosyaya veya
  ortama erisme.
- Yanitlari Turkce yaz, sayisal sonuclari net bir cumle ile sun.
- Cevabin sonunda "Yontem:" satirinda hangi pandas ifadesinin
  kullanildigini belirt.
- Eger sorunun cevabi DataFrame'de yoksa "Bu bilgi tabloda yok"
  cevabini ver.
"""


@dataclass(frozen=True)
class DataFrameSummary:
    """LLM'siz deterministik ozet."""

    rows: int
    columns: list[str]
    dtypes: dict[str, str]
    head: list[dict[str, Any]]
    describe: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class AgentAnswer:
    """Agent'in dondurdugu yapilandirilmis cevap."""

    answer: str
    raw_output: str


def summarize_dataframe(df: pd.DataFrame, *, head_rows: int = 5) -> DataFrameSummary:
    """Pandas DataFrame icin LLM cagrisi olmadan deterministik ozet uret."""
    head_records: list[dict[str, Any]] = (
        df.head(head_rows).fillna("").to_dict(orient="records")
    )

    describe_df = df.describe(include="all", datetime_is_numeric=False).fillna("")
    describe: dict[str, dict[str, Any]] = {
        str(col): {str(idx): _coerce(val) for idx, val in describe_df[col].items()}
        for col in describe_df.columns
    }

    dtypes = {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    return DataFrameSummary(
        rows=int(len(df)),
        columns=[str(c) for c in df.columns],
        dtypes=dtypes,
        head=head_records,
        describe=describe,
    )


def _coerce(value: Any) -> Any:
    """JSON-serileştirilebilir hale getir."""
    if pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    try:
        return float(value) if isinstance(value, (int, float)) else value
    except (TypeError, ValueError):
        return str(value)


class PandasQaAgent:
    """LangChain pandas DataFrame agent sarmalayicisi."""

    def __init__(
        self,
        llm: BaseLanguageModel,
        *,
        max_iterations: int = 8,
        verbose: bool = False,
    ) -> None:
        self._llm = llm
        self._max_iterations = max_iterations
        self._verbose = verbose

    def ask(self, df: pd.DataFrame, question: str) -> AgentAnswer:
        question = (question or "").strip()
        if not question:
            raise ValueError("Bos soru ile agent cagrilamaz.")

        agent = create_pandas_dataframe_agent(
            llm=self._llm,
            df=df,
            agent_type="zero-shot-react-description",
            prefix=_AGENT_PREFIX_TR,
            verbose=self._verbose,
            allow_dangerous_code=True,
            max_iterations=self._max_iterations,
            handle_parsing_errors=True,
            return_intermediate_steps=False,
        )

        log.info("PandasQaAgent.ask: soru='%s' satir=%d", question, len(df))
        result = agent.invoke({"input": question})
        raw = str(result.get("output", "")).strip()
        return AgentAnswer(answer=raw or "Bu bilgi tabloda yok", raw_output=raw)
