"""Document RAG pipeline for WMS project documentation."""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from result_formatter import render_doc_answer
from vector_config import DOCS_COLLECTION_NAME, build_chroma, collection_count

logger = logging.getLogger(__name__)

NO_INFO_ANSWER = "Bu konuda bilgi bulamadım"
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))
RAG_MAX_DISTANCE = float(os.getenv("RAG_MAX_DISTANCE", "1.15"))
RAG_NUM_PREDICT = int(os.getenv("RAG_NUM_PREDICT", "300"))

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
LLM_NUM_CTX = int(os.getenv("LLM_NUM_CTX", "4096"))

RAG_SYSTEM_PROMPT = """Sen WMS Dokuman Bilgi Asistani'sin.
Asagidaki BAGLAM bilgilerini kullanarak soruyu cevapla.
Cevabi sadece baglama dayandir. Bilgi baglamda yoksa tam olarak "Bu konuda bilgi bulamadım" de.
Uydurma, tahmin yapma ve baglam disi proje bilgisi ekleme.
Cevabi kisa, is odakli ve Markdown uyumlu yaz."""

RAG_USER_PROMPT = """BAGLAM:
{context}

SORU:
{question}

CEVAP:"""


@dataclass(frozen=True)
class DocSource:
    source_path: str
    title: str | None = None
    section: str | None = None
    chunk_id: str | None = None
    score: float | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "source_path": self.source_path,
            "title": self.title,
            "section": self.section,
            "chunk_id": self.chunk_id,
        }
        if self.score is not None:
            payload["score"] = self.score
        return payload


@dataclass(frozen=True)
class RagResult:
    answer: str
    rendered_answer: str
    sources: list[dict[str, Any]]
    debug: dict[str, Any]


class RagPipeline:
    def __init__(self, chroma: Any | None = None, chain: Any | None = None) -> None:
        self._chroma = chroma
        self._chain = chain or self._build_chain()

    def _build_chain(self) -> Any:
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0,
            top_p=1.0,
            num_ctx=LLM_NUM_CTX,
            num_predict=RAG_NUM_PREDICT,
            timeout=LLM_TIMEOUT,
        )
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", RAG_SYSTEM_PROMPT),
                ("human", RAG_USER_PROMPT),
            ]
        )
        return prompt | llm | StrOutputParser()

    def run(self, question: str) -> RagResult:
        try:
            chroma = self._chroma or build_chroma(collection_name=DOCS_COLLECTION_NAME)
            count = collection_count(chroma)
            if count == 0:
                return self._no_context("docs collection bos", collection_count=count)

            docs_and_scores = chroma.similarity_search_with_score(question, k=RAG_TOP_K)
        except Exception as exc:  # noqa: BLE001
            logger.warning("RAG retrieval basarisiz: %s", exc)
            return self._no_context(str(exc))

        filtered = [
            (doc, float(distance))
            for doc, distance in docs_and_scores
            if float(distance) <= RAG_MAX_DISTANCE
        ]
        if not filtered:
            return self._no_context(
                "ilgili chunk bulunamadi",
                matches=[
                    {
                        "distance": round(float(distance), 4),
                        "source_path": doc.metadata.get("source_path"),
                    }
                    for doc, distance in docs_and_scores
                ],
            )

        context = self._render_context(filtered)
        raw_answer = self._chain.invoke({"context": context, "question": question})
        answer = _clean_answer(raw_answer)
        if _is_no_info(answer):
            return RagResult(
                answer=NO_INFO_ANSWER,
                rendered_answer=NO_INFO_ANSWER,
                sources=[],
                debug={
                    "rag_collection": DOCS_COLLECTION_NAME,
                    "used_chunks": len(filtered),
                    "llm_reported_no_info": True,
                },
            )

        sources = self._sources(filtered)
        rendered = render_doc_answer(answer, sources)
        return RagResult(
            answer=answer,
            rendered_answer=rendered,
            sources=sources,
            debug={
                "rag_collection": DOCS_COLLECTION_NAME,
                "used_chunks": len(filtered),
                "max_distance": RAG_MAX_DISTANCE,
                "matches": [
                    {
                        "distance": round(score, 4),
                        "source_path": doc.metadata.get("source_path"),
                        "section": doc.metadata.get("section"),
                    }
                    for doc, score in filtered
                ],
            },
        )

    def _render_context(self, docs_and_scores: list[tuple[Any, float]]) -> str:
        blocks: list[str] = []
        for index, (doc, _score) in enumerate(docs_and_scores, 1):
            meta = doc.metadata
            label = " / ".join(
                part
                for part in [
                    str(meta.get("source_path") or ""),
                    str(meta.get("section") or ""),
                ]
                if part
            )
            blocks.append(f"[{index}] Kaynak: {label}\n{doc.page_content}")
        return "\n\n---\n\n".join(blocks)

    def _sources(self, docs_and_scores: list[tuple[Any, float]]) -> list[dict[str, Any]]:
        seen: set[tuple[str, str | None]] = set()
        sources: list[dict[str, Any]] = []
        for doc, score in docs_and_scores:
            meta = doc.metadata
            key = (str(meta.get("source_path") or ""), meta.get("section"))
            if key in seen:
                continue
            seen.add(key)
            sources.append(
                DocSource(
                    source_path=key[0],
                    title=meta.get("title"),
                    section=meta.get("section"),
                    chunk_id=meta.get("chunk_id"),
                    score=round(score, 4),
                ).as_dict()
            )
        return sources

    def _no_context(self, reason: str, **debug: Any) -> RagResult:
        return RagResult(
            answer=NO_INFO_ANSWER,
            rendered_answer=NO_INFO_ANSWER,
            sources=[],
            debug={
                "rag_collection": DOCS_COLLECTION_NAME,
                "no_context_reason": reason,
                **debug,
            },
        )


def _clean_answer(text: str) -> str:
    cleaned = text.strip()
    cleaned = re.sub(r"^(Cevap|Yanıt|Yanit)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip() or NO_INFO_ANSWER


def _is_no_info(answer: str) -> bool:
    normalized = answer.strip().rstrip(".").lower()
    return normalized == NO_INFO_ANSWER.lower()


_rag_pipeline: RagPipeline | None = None


def get_rag_pipeline() -> RagPipeline:
    global _rag_pipeline
    if _rag_pipeline is None:
        _rag_pipeline = RagPipeline()
    return _rag_pipeline
