"""
LangChain LCEL pipeline'ı.

Akış:
    soru + history
        -> SQL üret  (ChatOllama, low-temp, few-shot)
        -> clean & validate (sql_guard)
        -> execute (SQLAlchemy)
            -> hata olursa: self-correction loop (max N iter)
        -> sonuç + soru -> doğal dil cevap üret (ikinci LLM çağrısı)
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

from prompts import (
    ANSWER_GENERATION_PROMPT,
    SCHEMA_DESCRIPTION,
    SQL_CORRECTION_PROMPT,
    SQL_SYSTEM_PROMPT,
    SQL_USER_PROMPT,
    render_few_shot_block,
)
from sql_guard import SqlValidationError, clean_and_validate

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------------
# Konfig
# ----------------------------------------------------------------------------

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Cevap üretimi için ayrı (ve daha küçük) bir model kullanılabilir
OLLAMA_ANSWER_MODEL = os.getenv("OLLAMA_ANSWER_MODEL", OLLAMA_MODEL)
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
MAX_CORRECTION_ATTEMPTS = int(os.getenv("MAX_CORRECTION_ATTEMPTS", "2"))
RESULT_ROW_PREVIEW = int(os.getenv("RESULT_ROW_PREVIEW", "20"))


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
        num_ctx=LLM_NUM_CTX,
        timeout=LLM_TIMEOUT,
    )


def build_answer_llm() -> ChatOllama:
    return ChatOllama(
        model=OLLAMA_ANSWER_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=0.2,
        num_ctx=LLM_NUM_CTX,
        timeout=LLM_TIMEOUT,
    )


# ----------------------------------------------------------------------------
# Promptlar (LCEL)
# ----------------------------------------------------------------------------

def build_sql_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages(
        [
            ("system", SQL_SYSTEM_PROMPT),
            ("human", SQL_USER_PROMPT),
        ]
    ).partial(
        schema=SCHEMA_DESCRIPTION,
        examples=render_few_shot_block(),
    )


def build_correction_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("human", SQL_CORRECTION_PROMPT)]).partial(
        schema=SCHEMA_DESCRIPTION
    )


def build_answer_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([("human", ANSWER_GENERATION_PROMPT)])


# ----------------------------------------------------------------------------
# Çekirdek pipeline
# ----------------------------------------------------------------------------

@dataclass
class SorguSonucu:
    soru: str
    uretilen_sql: str
    raw_sonuc: Any
    cevap: str
    deneme_sayisi: int
    duzeltme_logu: list[str]


class WmsAiPipeline:
    def __init__(self) -> None:
        self.db = build_db()
        self.sql_llm = build_sql_llm()
        self.answer_llm = build_answer_llm()
        self.sql_chain = build_sql_prompt() | self.sql_llm | StrOutputParser()
        self.correction_chain = build_correction_prompt() | self.sql_llm | StrOutputParser()
        self.answer_chain = build_answer_prompt() | self.answer_llm | StrOutputParser()

    # --- adımlar ---

    def _generate_sql(self, soru: str, history: str) -> str:
        raw = self.sql_chain.invoke({"soru": soru, "history": history})
        logger.debug("LLM raw SQL output: %s", raw)
        return clean_and_validate(raw)

    def _correct_sql(self, soru: str, hatalı_sql: str, hata: str) -> str:
        raw = self.correction_chain.invoke(
            {"soru": soru, "sql": hatalı_sql, "hata": hata}
        )
        logger.debug("LLM correction output: %s", raw)
        return clean_and_validate(raw)

    def _execute(self, sql: str) -> Any:
        # SQLDatabase.run güvenli; ama biz zaten guard'ladık.
        return self.db.run(sql, include_columns=True)

    def _generate_answer(self, soru: str, sql: str, sonuc: Any) -> str:
        preview = self._truncate_result(sonuc)
        return self.answer_chain.invoke({"soru": soru, "sql": sql, "sonuc": preview})

    @staticmethod
    def _truncate_result(sonuc: Any) -> str:
        text = str(sonuc)
        # Çok büyük sonuçlar context'i bozar
        if len(text) > 4000:
            return text[:4000] + "\n... (sonuç kırpıldı)"
        return text

    # --- entrypoint ---

    def run(self, soru: str, history: str = "(önceki konuşma yok)") -> SorguSonucu:
        attempts = 0
        log: list[str] = []
        sql = self._generate_sql(soru, history)
        attempts += 1
        log.append(f"deneme-{attempts}: {sql}")

        last_error: Exception | None = None
        sonuc: Any = None
        for _ in range(MAX_CORRECTION_ATTEMPTS + 1):
            try:
                sonuc = self._execute(sql)
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

        if last_error is not None:
            raise RuntimeError(
                f"SQL {attempts} denemede çalıştırılamadı. Son hata: {last_error}"
            )

        cevap = self._generate_answer(soru, sql, sonuc)

        return SorguSonucu(
            soru=soru,
            uretilen_sql=sql,
            raw_sonuc=sonuc,
            cevap=cevap.strip(),
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
