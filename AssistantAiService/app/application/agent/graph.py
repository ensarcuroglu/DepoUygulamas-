"""LangGraph StateGraph builder for the depo asistani.

Topoloji:

    START -> prepare_context -> llm -> dispatcher
                                  |       |
                                  v       v
                                 END    (HITL ise END, degilse llm)

Checkpointer enjekte edilebilir: production'da AsyncSqliteSaver, test'lerde
MemorySaver ya da None.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.application.agent.nodes import (
    make_llm_node,
    make_tool_dispatcher_node,
    prepare_context_node,
    route_after_dispatcher,
    route_after_llm,
)
from app.application.agent.state import AssistantState
from app.application.agent.tools import LocalToolRegistry, default_registry


def build_graph(
    llm: BaseChatModel,
    *,
    registry: LocalToolRegistry | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Compile and return a runnable LangGraph state machine.

    Args:
        llm: Already-constructed chat model (ChatOllama or FakeListChatModel).
        registry: Override the default tool registry (test isolation).
        checkpointer: Optional state persister; if None, the graph is stateless
            (each invocation starts fresh — useful for tests).
    """
    registry = registry or default_registry()

    builder: StateGraph = StateGraph(AssistantState)

    builder.add_node("prepare_context", prepare_context_node)
    builder.add_node("llm", make_llm_node(llm, registry))
    builder.add_node("dispatcher", make_tool_dispatcher_node(registry))

    builder.add_edge(START, "prepare_context")
    builder.add_edge("prepare_context", "llm")

    builder.add_conditional_edges(
        "llm",
        route_after_llm,
        {"dispatcher": "dispatcher", "end": END},
    )

    builder.add_conditional_edges(
        "dispatcher",
        route_after_dispatcher,
        {"llm": "llm", "end": END},
    )

    return builder.compile(checkpointer=checkpointer)
