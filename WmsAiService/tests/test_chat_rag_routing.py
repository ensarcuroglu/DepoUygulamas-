from __future__ import annotations

from types import SimpleNamespace

import pytest

from chat_orchestrator import ChatOrchestrator
from docs_rag import NO_INFO_ANSWER, RagPipeline, RagResult
from result_formatter import render_doc_answer
from route_examples import ROUTE_DOCS, ROUTE_SQL
from semantic_router import RouteDecision, SemanticRouter
from slash_commands import SlashCommandError, parse_slash_command


def test_parse_sql_slash_command_forces_sql() -> None:
    parsed = parse_slash_command("/sql Dun kac palet geldi?")

    assert parsed.forced_route == ROUTE_SQL
    assert parsed.question == "Dun kac palet geldi?"


def test_parse_docs_slash_command_forces_docs() -> None:
    parsed = parse_slash_command("/docs FEFO mantigi nedir?")

    assert parsed.forced_route == ROUTE_DOCS
    assert parsed.question == "FEFO mantigi nedir?"


def test_parse_unknown_slash_command_rejected() -> None:
    with pytest.raises(SlashCommandError) as exc:
        parse_slash_command("/help FEFO")

    assert "/docs" in exc.value.allowed_commands
    assert "/sql" in exc.value.allowed_commands


def test_semantic_router_keyword_fallback_routes_docs() -> None:
    router = SemanticRouter(chroma=object())

    decision = router.route("Sistem nasıl çalışır?")

    assert decision.route == ROUTE_DOCS
    assert decision.debug["router_backend"] == "keyword_fallback"


def test_rag_no_context_returns_no_info() -> None:
    class EmptyCollection:
        def count(self) -> int:
            return 0

    class EmptyChroma:
        _collection = EmptyCollection()

    pipeline = RagPipeline(chroma=EmptyChroma(), chain=object())

    result = pipeline.run("FEFO nedir?")

    assert result.answer == NO_INFO_ANSWER
    assert result.sources == []
    assert "no_context_reason" in result.debug


def test_render_doc_answer_appends_markdown_sources() -> None:
    answer = render_doc_answer(
        "FEFO en eski SKT'li urunun once cikmasidir.",
        [{"source_path": "DOCS/agent/ai-services.md", "section": "WmsAiService"}],
    )

    assert "**Kaynaklar**" in answer
    assert "`DOCS/agent/ai-services.md`" in answer


def test_chat_orchestrator_forced_docs_skips_router_and_sql() -> None:
    class FailingRouter:
        def route(self, _question):
            raise AssertionError("router should be bypassed")

    class FailingSql:
        def run(self, *_args, **_kwargs):
            raise AssertionError("sql should be bypassed")

    class FakeRag:
        def run(self, question):
            return RagResult(
                answer="FEFO cevabi",
                rendered_answer="FEFO cevabi",
                sources=[{"source_path": "CLAUDE.md"}],
                debug={"ok": True},
            )

    orchestrator = ChatOrchestrator(
        sql_pipeline=FailingSql(),
        rag_pipeline=FakeRag(),
        semantic_router=FailingRouter(),
    )

    result = orchestrator.run("/docs FEFO mantigi nedir?", history="", verbose=False)

    assert result.route == ROUTE_DOCS
    assert result.route_source == "slash_command"
    assert result.uretilen_sql is None
    assert result.sources == [{"source_path": "CLAUDE.md"}]


def test_chat_orchestrator_semantic_sql_branch() -> None:
    class FakeRouter:
        def route(self, question):
            assert question == "Aktif palet sayisi kac?"
            return RouteDecision(
                route=ROUTE_SQL,
                route_source="semantic_router",
                confidence=0.8,
                debug={"router_backend": "test"},
            )

    class FakeSql:
        def run(self, question, *, history, verbose):
            assert question == "Aktif palet sayisi kac?"
            assert history == "history"
            assert verbose is False
            return SimpleNamespace(
                soru=question,
                cevap="Toplam 3 palet bulunuyor.",
                uretilen_sql="SELECT COUNT(*) AS palet_sayisi FROM ai_palet_view;",
                deneme_sayisi=1,
                structured=None,
                duzeltme_logu=[],
            )

    class FailingRag:
        def run(self, _question):
            raise AssertionError("rag should be bypassed")

    orchestrator = ChatOrchestrator(
        sql_pipeline=FakeSql(),
        rag_pipeline=FailingRag(),
        semantic_router=FakeRouter(),
    )

    result = orchestrator.run("Aktif palet sayisi kac?", history="history", verbose=False)

    assert result.route == ROUTE_SQL
    assert result.route_source == "semantic_router"
    assert result.uretilen_sql.startswith("SELECT")
