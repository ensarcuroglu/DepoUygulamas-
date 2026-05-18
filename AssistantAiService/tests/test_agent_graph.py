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
            else ["tarih_saat_simdi", "yerlestirme_konum_degistir"],
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
            make_ai(content="Maalesef sorulan aleti bulamadim."),
        ]
    )
    graph = make_graph(fake)

    state = await graph.ainvoke(_input_state())

    tool_msgs = [m for m in state["messages"] if isinstance(m, ToolMessage)]
    assert any("bulunamadi" in t.content for t in tool_msgs)
    last_ai = [m for m in state["messages"] if isinstance(m, AIMessage)][-1]
    assert last_ai.content.startswith("Maalesef")


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
