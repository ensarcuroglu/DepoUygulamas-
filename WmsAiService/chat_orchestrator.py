"""Unified chat orchestration for SQL and documentation RAG routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

try:
    from langchain_core.runnables import RunnableBranch, RunnableLambda
except ModuleNotFoundError:  # pragma: no cover - local tests may omit runtime deps
    class RunnableLambda:
        def __init__(self, func):
            self._func = func

        def invoke(self, payload):
            return self._func(payload)

    class RunnableBranch:
        def __init__(self, *branches):
            self._branches = branches

        def invoke(self, payload):
            *conditional, default = self._branches
            for condition, runnable in conditional:
                if condition(payload):
                    return runnable.invoke(payload)
            return default.invoke(payload)

from docs_rag import RagResult, get_rag_pipeline
from route_examples import ROUTE_DOCS, ROUTE_SQL
from semantic_router import RouteDecision, get_semantic_router
from slash_commands import (
    ROUTE_SOURCE_SEMANTIC,
    ROUTE_SOURCE_SLASH,
    parse_slash_command,
)


@dataclass(frozen=True)
class ChatRunResult:
    soru: str
    cevap: str
    uretilen_sql: str | None
    route: str
    route_source: str
    confidence: float | None
    sources: list[dict[str, Any]]
    deneme_sayisi: int
    debug: dict[str, Any]
    structured: Any | None = None
    duzeltme_logu: list[str] | None = None


@dataclass(frozen=True)
class _ChatDecision:
    question: str
    route: str
    route_source: str
    confidence: float | None
    debug: dict[str, Any]


class ChatOrchestrator:
    def __init__(
        self,
        *,
        sql_pipeline: Any | None = None,
        rag_pipeline: Any | None = None,
        semantic_router: Any | None = None,
    ) -> None:
        if sql_pipeline is None:
            from chains import get_pipeline

            sql_pipeline = get_pipeline()
        self._sql_pipeline = sql_pipeline
        self._rag_pipeline = rag_pipeline or get_rag_pipeline()
        self._semantic_router = semantic_router or get_semantic_router()
        self._branch = RunnableBranch(
            (
                lambda payload: payload["decision"].route == ROUTE_DOCS,
                RunnableLambda(self._run_docs),
            ),
            RunnableLambda(self._run_sql),
        )

    def run(
        self,
        soru: str,
        *,
        history: str,
        verbose: bool = False,
    ) -> ChatRunResult:
        decision = self._decide_route(soru)
        return self._branch.invoke(
            {
                "decision": decision,
                "history": history,
                "verbose": verbose,
            }
        )

    def _decide_route(self, soru: str) -> _ChatDecision:
        parsed = parse_slash_command(soru)
        if parsed.forced_route:
            return _ChatDecision(
                question=parsed.question,
                route=parsed.forced_route,
                route_source=ROUTE_SOURCE_SLASH,
                confidence=1.0,
                debug={"command": parsed.command},
            )

        route_decision: RouteDecision = self._semantic_router.route(parsed.question)
        return _ChatDecision(
            question=parsed.question,
            route=route_decision.route,
            route_source=ROUTE_SOURCE_SEMANTIC,
            confidence=route_decision.confidence,
            debug=route_decision.debug,
        )

    def _run_sql(self, payload: dict[str, Any]) -> ChatRunResult:
        decision: _ChatDecision = payload["decision"]
        sonuc = self._sql_pipeline.run(
            decision.question,
            history=payload["history"],
            verbose=payload["verbose"],
        )
        return ChatRunResult(
            soru=sonuc.soru,
            cevap=sonuc.cevap,
            uretilen_sql=sonuc.uretilen_sql,
            route=ROUTE_SQL,
            route_source=decision.route_source,
            confidence=decision.confidence,
            sources=[],
            deneme_sayisi=sonuc.deneme_sayisi,
            debug={"router": decision.debug},
            structured=sonuc.structured,
            duzeltme_logu=sonuc.duzeltme_logu,
        )

    def _run_docs(self, payload: dict[str, Any]) -> ChatRunResult:
        decision: _ChatDecision = payload["decision"]
        result: RagResult = self._rag_pipeline.run(decision.question)
        return ChatRunResult(
            soru=decision.question,
            cevap=result.rendered_answer,
            uretilen_sql=None,
            route=ROUTE_DOCS,
            route_source=decision.route_source,
            confidence=decision.confidence,
            sources=result.sources,
            deneme_sayisi=1,
            debug={"router": decision.debug, "rag": result.debug},
        )


_chat_orchestrator: ChatOrchestrator | None = None


def get_chat_orchestrator() -> ChatOrchestrator:
    global _chat_orchestrator
    if _chat_orchestrator is None:
        _chat_orchestrator = ChatOrchestrator()
    return _chat_orchestrator
