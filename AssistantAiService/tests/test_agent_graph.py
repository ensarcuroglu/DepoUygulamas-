"""LangGraph agent topology tests (HTTP'siz).

TestClient dahil etmeden agent davranisini test ediyoruz; graph dogrudan
fake_llm ile insa edilir, `ainvoke` cagrilir. Boylece lifespan, middleware,
ve HTTP serileme katmanlarindan bagimsiz olarak agent loop'unu izole
dogruluyoruz.
"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.checkpoint.memory import InMemorySaver

from app.core.config import get_settings
from tests.conftest import make_ai, make_fake_model

pytestmark = pytest.mark.asyncio


def _input_state(
    soru: str = "merhaba",
    *,
    rol: str = "depocu",
    izinli: list[str] | None = None,
) -> dict:
    return {
        "messages": [HumanMessage(content=soru)],
        "user_context": {
            "kullanici_id": 7,
            "rol": rol,
            "aktif_gorev_id": None,
            "aktif_ekran": "terminal",
            "izinli_tool_idleri": izinli
            if izinli is not None
            else [
                "tarih_saat_simdi",
                "palet_sorgula",
                "palet_raf_degistir",
                "yerlestirme_konum_degistir",
            ],
        },
        "proposed_action": None,
        "debug": {},
    }


# ---------------------------------------------------------------------------
# 1) No tool path
# ---------------------------------------------------------------------------

async def test_graph_plain_text_route_skips_dispatcher(make_graph):
    fake = make_fake_model([make_ai(content="merhaba (test)")])
    graph = make_graph(fake)

    state = await graph.ainvoke(_input_state("selam"))

    assert state["proposed_action"] is None
    last = state["messages"][-1]
    assert isinstance(last, AIMessage)
    assert last.content == "merhaba (test)"
    # debug.tool_iterations dispatcher girilmediginde set edilmemis olmali
    assert "tool_iterations" not in (state.get("debug") or {})


# ---------------------------------------------------------------------------
# 2) Read-only tool loop
# ---------------------------------------------------------------------------

async def test_graph_readonly_tool_executes_and_summarizes(make_graph):
    """LLM read-only tool secince executor calistirilir, tool_message eklenir,
    sonra LLM ikinci kez cagrilip ozet uretir."""
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[
                    {"name": "tarih_saat_simdi", "id": "c1", "args": {}}
                ],
            ),
            make_ai(content="Su an sabah saatleri."),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(_input_state("saat kac"))

    assert state["proposed_action"] is None
    # En son AIMessage 2. LLM cagrisinin ozetidir
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    assert last_ai.content == "Su an sabah saatleri."
    # Mesaj zincirinde bir ToolMessage olmali
    tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_msgs) == 1
    # Executor'in donduğü JSON içinde gun_adi alani var
    assert "gun_adi" in tool_msgs[0].content


# ---------------------------------------------------------------------------
# 3) HITL short-circuit
# ---------------------------------------------------------------------------

async def test_graph_hitl_tool_short_circuits_to_end(make_graph):
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[
                    {
                        "name": "yerlestirme_konum_degistir",
                        "id": "c1",
                        "args": {"gorev_id": 42, "yeni_konum_kodu": "B-12-3"},
                    }
                ],
            ),
            # Bu 2. cevap CAGIRILMAMALI; HITL kestirimi END'e gider.
            make_ai(content="BU CAGRILMAMALIDIR"),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(_input_state("A koridoru tikali"))

    pa = state["proposed_action"]
    assert pa is not None
    assert pa["tool_id"] == "yerlestirme_konum_degistir"
    assert pa["params"] == {"gorev_id": 42, "yeni_konum_kodu": "B-12-3"}
    # LLM ikinci kez cagrilmamali — cursor 1'de durmali (FakeChatModel internal i)
    assert fake.i == 1, "LLM ikinci kez cagrilmis; HITL kestirimi calismadi"


# ---------------------------------------------------------------------------
# 4) Unknown tool name → graceful error tool message
# ---------------------------------------------------------------------------

async def test_graph_unknown_tool_returns_friendly_tool_message(make_graph):
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[
                    {"name": "yok_olan_alet", "id": "c1", "args": {}}
                ],
            ),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(_input_state())

    tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    assert any("reddedildi" in t.content for t in tool_msgs)
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    assert "kullanamiyorum" in last_ai.content
    assert state["debug"]["fallback_reason"] == "unknown_tool"


async def test_graph_missing_tool_args_asks_for_clarification(make_graph):
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[{"name": "palet_sorgula", "id": "c1", "args": {}}],
            ),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(_input_state("palete bak"))

    assert state["proposed_action"] is None
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    assert "palet_no" in last_ai.content
    assert state["debug"]["fallback_reason"] == "validation_error"


async def test_graph_unauthorized_tool_is_blocked(make_graph):
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[
                    {
                        "name": "karantinaya_al",
                        "id": "c1",
                        "args": {"palet_no": "P-1", "neden": "hasarli"},
                    }
                ],
            ),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(
        _input_state(rol="depocu", izinli=["karantinaya_al"])
    )

    assert state["proposed_action"] is None
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    assert "Bu rol ile" in last_ai.content
    assert state["debug"]["fallback_reason"] == "unauthorized_tool"


async def test_graph_hitl_args_are_repaired_before_proposed_action(make_graph):
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[
                    {
                        "name": "palet_raf_degistir",
                        "id": "c1",
                        "args": {"palet_barkodu": "P-1", "yeni_konum": "R-2"},
                    }
                ],
            ),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(
        _input_state(
            "P-1 paletini R-2 rafina al",
            izinli=["palet_raf_degistir"],
        )
    )

    assert state["proposed_action"] == {
        "tool_id": "palet_raf_degistir",
        "params": {"palet_no": "P-1", "yeni_raf_kodu": "R-2"},
        "ozet": "Palet P-1 icin yeni raf: R-2",
    }


async def test_graph_max_tool_iterations_stops_loop(make_graph, monkeypatch):
    monkeypatch.setenv("MAX_TOOL_ITERATIONS", "1")
    get_settings.cache_clear()
    fake = make_fake_model(
        [
            make_ai(
                content="",
                tool_calls=[{"name": "tarih_saat_simdi", "id": "c1", "args": {}}],
            ),
            make_ai(
                content="",
                tool_calls=[{"name": "tarih_saat_simdi", "id": "c2", "args": {}}],
            ),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(_input_state("saat kac"))

    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    assert "dongusu sinirina" in last_ai.content
    assert state["debug"]["fallback_reason"] == "max_tool_iterations"


# ---------------------------------------------------------------------------
# 5) Session memory continuity via checkpointer
# ---------------------------------------------------------------------------

async def test_graph_thread_continues_history(make_graph):
    """Ayni thread_id ile yapilan ikinci cagri ilk turun mesajlarini gormeli."""
    fake = make_fake_model(
        [
            make_ai(content="ilk cevap"),
            make_ai(content="ikinci cevap"),
        ]
    )
    graph = make_graph(fake, checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "user-7:s1"}}

    state1 = await graph.ainvoke(_input_state("ilk soru"), config=config)
    state2 = await graph.ainvoke(
        {
            "messages": [HumanMessage(content="ikinci soru")],
            "user_context": state1["user_context"],
        },
        config=config,
    )

    # Ikinci turde mesaj zinciri ilk turun mesajlarini icermeli
    contents = [getattr(m, "content", "") for m in state2["messages"]]
    assert "ilk soru" in contents
    assert "ilk cevap" in contents
    assert "ikinci soru" in contents
    assert "ikinci cevap" in contents
