"""LangGraph node implementations.

Tek bir dosyada uc node:
- `prepare_context_node`: ilk turde sistem mesajini state.messages'in basina
  enjekte eder ve `debug` alanini baslatir.
- `llm_node`: LLM'i (bind_tools edilmis) state.messages ile cagirir. Donen
  AIMessage state'e eklenir.
- `tool_dispatcher_node`: son AIMessage'taki tool_calls'lari yakalar;
  - HITL aletler -> proposed_action'a donusturulup END'e gidilir
  - Read-only aletler executor uzerinden calistirilir ve ToolMessage
    olusturulur, graph llm'e geri doner.

Yonlendirme `graph.py`'da `tools_condition`/conditional edge ile yapilir.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage

from app.application.agent.prompts import render_system_prompt
from app.application.agent.state import AssistantState
from app.application.agent.tools import LocalToolRegistry, compose_proposed_action_ozet

log = logging.getLogger(__name__)

# Cevre dongulerini engelle: bir kullanici turunde en fazla 3 tool roundtrip.
MAX_TOOL_ITERATIONS = 3


# ---------------------------------------------------------------------------
# prepare_context
# ---------------------------------------------------------------------------

def prepare_context_node(state: AssistantState) -> dict[str, Any]:
    """Bu thread'in ilk turunde sistem promptunu state'e enjekte et."""
    messages = state.get("messages", []) or []
    if any(isinstance(m, SystemMessage) for m in messages):
        return {}  # zaten enjekte edilmis (checkpointer restore'u)
    user_context = state.get("user_context") or {}
    system = SystemMessage(content=render_system_prompt(user_context))
    return {
        "messages": [system],
        "debug": {**(state.get("debug") or {}), "system_prompt_injected": True},
    }


# ---------------------------------------------------------------------------
# llm_node
# ---------------------------------------------------------------------------

def make_llm_node(
    llm: BaseChatModel,
    registry: LocalToolRegistry,
):
    """Closure: dinamik olarak rol+izin filtreli tools bind ederek LLM cagirir."""

    async def llm_node(state: AssistantState) -> dict[str, Any]:
        user_context = state.get("user_context") or {}
        rol = user_context.get("rol", "")
        izinli = user_context.get("izinli_tool_idleri") or None

        tools = registry.to_langchain_tools(rol=rol, izinli_tool_idleri=izinli)
        bound_llm = llm.bind_tools(tools) if tools else llm

        messages: list[BaseMessage] = state.get("messages", []) or []
        ai_msg = await bound_llm.ainvoke(messages)
        return {"messages": [ai_msg]}

    return llm_node


# ---------------------------------------------------------------------------
# tool_dispatcher_node
# ---------------------------------------------------------------------------

def make_tool_dispatcher_node(registry: LocalToolRegistry):
    """Closure: tool_calls'lari ayirip HITL kestiriminde proposed_action yazar."""

    async def tool_dispatcher_node(state: AssistantState) -> dict[str, Any]:
        messages = state.get("messages", []) or []
        last = messages[-1] if messages else None
        if not isinstance(last, AIMessage) or not last.tool_calls:
            return {}

        # Iterasyon sayisini debug'a yaz (cevre dongusu telemetrisi)
        debug = dict(state.get("debug") or {})
        debug["tool_iterations"] = debug.get("tool_iterations", 0) + 1

        # Once HITL var mi? Varsa ilkini al ve END'e git.
        for call in last.tool_calls:
            spec = registry.get(call["name"])
            if spec is not None and spec.hitl:
                ozet = compose_proposed_action_ozet(spec.tool_id, call.get("args") or {})
                return {
                    "proposed_action": {
                        "tool_id": spec.tool_id,
                        "params": call.get("args") or {},
                        "ozet": ozet,
                    },
                    # Tutarli mesaj geçmişi: model gormeli ki bir HITL beklemede.
                    "messages": [
                        ToolMessage(
                            content=(
                                f"[HITL ASKIDA] {spec.tool_id} kullanici onayina iletildi."
                            ),
                            tool_call_id=call["id"],
                        )
                    ],
                    "debug": debug,
                }

        # Hicbiri HITL degil: read-only batch'i sirayla calistir.
        new_messages: list[BaseMessage] = []
        for call in last.tool_calls:
            spec = registry.get(call["name"])
            if spec is None:
                new_messages.append(
                    ToolMessage(
                        content=f"Alet bulunamadi: {call['name']}",
                        tool_call_id=call["id"],
                    )
                )
                continue
            try:
                assert spec.executor is not None  # read-only guarantee
                sonuc = await spec.executor(**(call.get("args") or {}))
                content = json.dumps(sonuc, ensure_ascii=False, default=str)
            except Exception as exc:  # noqa: BLE001 - tool sozlesmesi disindaki her hata
                log.warning("Tool '%s' hatasi: %s", spec.tool_id, exc)
                content = f"Alet hatasi: {exc}"
            new_messages.append(
                ToolMessage(content=content, tool_call_id=call["id"])
            )
        return {"messages": new_messages, "debug": debug}

    return tool_dispatcher_node


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------

def route_after_llm(state: AssistantState) -> str:
    """Conditional edge: tool_calls varsa dispatcher'a, yoksa END."""
    messages = state.get("messages", []) or []
    last = messages[-1] if messages else None
    if isinstance(last, AIMessage) and last.tool_calls:
        return "dispatcher"
    return "end"


def route_after_dispatcher(state: AssistantState) -> str:
    """Conditional edge: HITL kestirimi varsa END, yoksa LLM'e dönüp ozetlet."""
    if state.get("proposed_action"):
        return "end"
    # Max tool iteration koruyucusu: sonsuz LLM<->tool dongusunu kes.
    iterations = (state.get("debug") or {}).get("tool_iterations", 0)
    if iterations >= MAX_TOOL_ITERATIONS:
        return "end"
    return "llm"
