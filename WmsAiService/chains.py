"""
LangChain LCEL pipeline’ı.

Akış:
    soru + history
        -> Dinamik Few-Shot: SemanticSimilarityExampleSelector (k=3, ChromaDB)
           kullanıcı sorusuna en yakın örnekleri seç
        -> SQL üret  (ChatOllama, temp=0, dinamik örneklerle)
        -> clean & validate (sql_guard)
        -> SQLAlchemy ile execute, structured rows + intent çıkar
            -> hata olursa: self-correction loop (max N iter)
        -> Answerer dispatch:
            EMPTY  -> sabit cümle
            SCALAR -> deterministik şablon (LLM yok)
            LIST   -> few-shot ile beslenen ChatOllama (temp=0, stop, num_predict)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from answerer import Answerer, ListAnswerLLM
from example_selector import select_and_format
from langfuse_tracing import langchain_config, safe_metadata
from prompts import (
    SCHEMA_DESCRIPTION,
    SQL_CORRECTION_PROMPT,
    SQL_SYSTEM_PROMPT,
    SQL_USER_PROMPT,
    render_few_shot_block,
)
from result_formatter import StructuredResult, execute_structured
from sql_guard import SqlValidationError, clean_and_validate

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Konfig
# ----------------------------------------------------------------------------

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_ANSWER_MODEL = os.getenv("OLLAMA_ANSWER_MODEL", OLLAMA_MODEL)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
ANSWER_NUM_PREDICT = int(os.getenv("ANSWER_NUM_PREDICT", "40"))
ANSWER_TOP_K = int(os.getenv("ANSWER_TOP_K", "1"))
ANSWER_REPEAT_PENALTY = float(os.getenv("ANSWER_REPEAT_PENALTY", "1.2"))
SQL_TOP_K = int(os.getenv("SQL_TOP_K", "1"))
SQL_REPEAT_PENALTY = float(os.getenv("SQL_REPEAT_PENALTY", "1.1"))
MAX_CORRECTION_ATTEMPTS = int(os.getenv("MAX_CORRECTION_ATTEMPTS", "2"))


# ----------------------------------------------------------------------------
# Veri tabanı
# ----------------------------------------------------------------------------

def build_db_uri() -> str:
    return (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        "?charset=utf8mb4"
    )


def build_db() -> SQLDatabase:
    return SQLDatabase.from_uri(
        build_db_uri(),
        include_tables=["ai_stok_durumu_view"],
        view_support=True,
        sample_rows_in_table_info=0,
    )


# ----------------------------------------------------------------------------
# LLM
# ----------------------------------------------------------------------------

def build_sql_llm() -> ChatOllama:
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
        top_k=SQL_TOP_K,
        top_p=1.0,
        repeat_penalty=SQL_REPEAT_PENALTY,
        num_ctx=LLM_NUM_CTX,
        timeout=LLM_TIMEOUT,
        # SQL çıktısı tek satır olmalı; modelin tekrar etmesini engelle
        stop=["\nSoru:", "\nKullanıcı:", "```\n```"],
    )


def build_answerer() -> Answerer:
    list_llm = ListAnswerLLM(
        model=OLLAMA_ANSWER_MODEL,
        base_url=OLLAMA_BASE_URL,
        timeout=LLM_TIMEOUT,
        num_ctx=LLM_NUM_CTX,
        num_predict=ANSWER_NUM_PREDICT,
        repeat_penalty=ANSWER_REPEAT_PENALTY,
        top_k=ANSWER_TOP_K,
    )
    return Answerer(list_llm=list_llm)


# ----------------------------------------------------------------------------
# Promptlar (LCEL)
# ----------------------------------------------------------------------------

def build_sql_prompt() -> ChatPromptTemplate:
    """SQL üretim promptu.

    {examples} artık partial değil — invoke anında dinamik olarak enjekte edilir.
    Bu sayede SemanticSimilarityExampleSelector ile seçilen örnekler
    her sorgu için farklı olabilir.
    """
    return ChatPromptTemplate.from_messages(
        [
            ("system", SQL_SYSTEM_PROMPT),
            ("human", SQL_USER_PROMPT),
        ]
    ).partial(
        schema=SCHEMA_DESCRIPTION,
    )


def build_correction_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("human", SQL_CORRECTION_PROMPT)]).partial(
        schema=SCHEMA_DESCRIPTION
    )


# ----------------------------------------------------------------------------
# Çekirdek pipeline
# ----------------------------------------------------------------------------

@dataclass
class SorguSonucu:
    soru: str
    uretilen_sql: str
    structured: StructuredResult
    cevap: str
    deneme_sayisi: int
    duzeltme_logu: list[str]


class WmsAiPipeline:
    def __init__(self) -> None:
        self.db = build_db()
        self.engine = self.db._engine  # SQLAlchemy engine — structured execute için
        self.sql_llm = build_sql_llm()
        self.sql_chain = build_sql_prompt() | self.sql_llm | StrOutputParser()
        self.correction_chain = build_correction_prompt() | self.sql_llm | StrOutputParser()
        self.answerer = build_answerer()

    # --- adımlar ---

    def _generate_sql(self, soru: str, history: str) -> str:
        """Dinamik few-shot ile SQL üret.

        1. SemanticSimilarityExampleSelector ile en yakın k=3 örneği seç
        2. Seçilen örnekleri formatlayıp prompt'a enjekte et
        3. LLM'den ham SQL al, temizle ve doğrula
        """
        examples = select_and_format(soru)
        if not examples:
            # Fallback: statik örnekler
            examples = render_few_shot_block()
            logger.debug("Dinamik örnek seçimi boş, statik fallback kullanılıyor.")

        raw = self.sql_chain.invoke(
            {"soru": soru, "history": history, "examples": examples},
            config=langchain_config(
                run_name="wms-ai.sql.generate",
                tags=["sql"],
                metadata=safe_metadata(operation="sql_generate", model=OLLAMA_MODEL),
            ),
        )
        logger.debug("LLM raw SQL output: %s", raw)
        return clean_and_validate(raw)

    def _correct_sql(self, soru: str, hatalı_sql: str, hata: str) -> str:
        raw = self.correction_chain.invoke(
            {"soru": soru, "sql": hatalı_sql, "hata": hata},
            config=langchain_config(
                run_name="wms-ai.sql.correct",
                tags=["sql", "correction"],
                metadata=safe_metadata(operation="sql_correction", model=OLLAMA_MODEL),
            ),
        )
        logger.debug("LLM correction output: %s", raw)
        return clean_and_validate(raw)

    def _execute(self, sql: str) -> StructuredResult:
        return execute_structured(self.engine, sql)

    # --- entrypoint ---

    def run(
        self,
        soru: str,
        history: str = "(önceki konuşma yok)",
        verbose: bool = False,
    ) -> SorguSonucu:
        attempts = 0
        log: list[str] = []
        sql = self._generate_sql(soru, history)
        attempts += 1
        log.append(f"deneme-{attempts}: {sql}")

        last_error: Exception | None = None
        structured: StructuredResult | None = None
        for _ in range(MAX_CORRECTION_ATTEMPTS + 1):
            try:
                structured = self._execute(sql)
                last_error = None
                break
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                err_text = str(exc)
                log.append(f"hata: {err_text[:300]}")
                if attempts > MAX_CORRECTION_ATTEMPTS:
                    break
                try:
                    sql = self._correct_sql(soru, sql, err_text)
                except SqlValidationError as ve:
                    log.append(f"correction-reddedildi: {ve}")
                    last_error = ve
                    break
                attempts += 1
                log.append(f"deneme-{attempts}: {sql}")

        if last_error is not None or structured is None:
            raise RuntimeError(
                f"SQL {attempts} denemede çalıştırılamadı. Son hata: {last_error}"
            )

        cevap = self.answerer.answer(soru, structured, verbose=verbose)
        log.append(f"intent: {structured.intent.value} (rows={structured.row_count})")

        return SorguSonucu(
            soru=soru,
            uretilen_sql=sql,
            structured=structured,
            cevap=cevap,
            deneme_sayisi=attempts,
            duzeltme_logu=log,
        )


# ----------------------------------------------------------------------------
# Singleton
# ----------------------------------------------------------------------------

_pipeline: WmsAiPipeline | None = None


def get_pipeline() -> WmsAiPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = WmsAiPipeline()
    return _pipeline
