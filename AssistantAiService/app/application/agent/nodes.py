"""LangGraph node implementations for the depo assistant."""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage, ToolMessage

from app.application.agent.prompts import render_system_prompt
from app.application.agent.state import AssistantState
from app.application.agent.tools import (
    LocalToolRegistry,
    build_runtime_context,
    compose_proposed_action_ozet,
    validate_tool_args,
)
from app.core.config import get_settings
from app.infrastructure.observability.langfuse_tracing import record_event

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# prepare_context
# ---------------------------------------------------------------------------

def prepare_context_node(state: AssistantState) -> dict[str, Any]:
    """Inject the system prompt once for this thread."""
    messages = state.get("messages", []) or []
    if any(isinstance(m, SystemMessage) for m in messages):
        return {}
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
    """Bind role-filtered tools dynamically and call the LLM."""

    async def llm_node(state: AssistantState) -> dict[str, Any]:
        user_context = state.get("user_context") or {}
        rol = user_context.get("rol", "")
        izinli = (
            user_context["izinli_tool_idleri"]
            if "izinli_tool_idleri" in user_context
            else None
        )

        runtime_context = build_runtime_context(user_context)
        tools = registry.to_langchain_tools(
            rol=rol,
            izinli_tool_idleri=izinli,
            runtime_context=runtime_context,
        )
        bound_llm = llm.bind_tools(tools) if tools else llm

        messages: list[BaseMessage] = state.get("messages", []) or []
        record_event(
            "assistant.llm.invoke",
            {
                "role": rol or "bilinmiyor",
                "bound_tool_count": len(tools),
            },
        )
        ai_msg = await bound_llm.ainvoke(messages)
        return {"messages": [ai_msg]}

    return llm_node


# ---------------------------------------------------------------------------
# tool_dispatcher_node
# ---------------------------------------------------------------------------

def make_tool_dispatcher_node(registry: LocalToolRegistry):
    """Validate tool calls, enforce HITL, and execute read-only tools."""

    async def tool_dispatcher_node(state: AssistantState) -> dict[str, Any]:
        messages = state.get("messages", []) or []
        last = messages[-1] if messages else None
        if not isinstance(last, AIMessage) or not last.tool_calls:
            return {}

        user_context = state.get("user_context") or {}
        rol = user_context.get("rol", "")
        allowlist = user_context.get("izinli_tool_idleri")
        allowed_ids = set(allowlist) if allowlist is not None else None

        debug = dict(state.get("debug") or {})
        current_iterations = int(debug.get("tool_iterations", 0))
        max_iterations = get_settings().max_tool_iterations
        if current_iterations >= max_iterations:
            debug.update(
                {
                    "fallback_reason": "max_tool_iterations",
                    "max_tool_iterations": max_iterations,
                }
            )
            record_event(
                "assistant.tool.fallback",
                {"fallback_reason": "max_tool_iterations", "max_iterations": max_iterations},
            )
            return {
                "messages": [
                    *[
                        ToolMessage(
                            content="Tool dongusu siniri nedeniyle arac calistirilmadi.",
                            tool_call_id=call["id"],
                        )
                        for call in last.tool_calls
                    ],
                    AIMessage(
                        content=(
                            "Arac dongusu sinirina ulasildi. Islemi durdurdum; "
                            "lutfen daha net tek bir depo talebiyle tekrar deneyin."
                        )
                    ),
                ],
                "debug": debug,
            }

        debug["tool_iterations"] = current_iterations + 1
        debug["selected_tools"] = [call["name"] for call in last.tool_calls]
        runtime_context = build_runtime_context(user_context)

        new_messages: list[BaseMessage] = []
        for call in last.tool_calls:
            spec = registry.get(call["name"])
            if spec is None:
                return _fallback_tool_response(
                    call,
                    debug,
                    fallback_reason="unknown_tool",
                    user_message=(
                        f"'{call['name']}' adli araci kullanamiyorum. "
                        "Lutfen palet, raf, stok, gorev veya onay gerektiren tek bir islem belirtin."
                    ),
                )

            if not spec.authorized_for(rol) or (
                allowed_ids is not None and spec.tool_id not in allowed_ids
            ):
                return _fallback_tool_response(
                    call,
                    debug,
                    fallback_reason="unauthorized_tool",
                    user_message=(
                        f"Bu rol ile '{spec.tool_id}' aracini kullanamam. "
                        "Yetkili bir kullanici ile ilerleyin veya izinli bir sorgu isteyin."
                    ),
                    tool_id=spec.tool_id,
                )

            validated_args, validation_error = validate_tool_args(
                spec,
                call.get("args") or {},
            )
            if validation_error is not None:
                field = _validation_field(validation_error)
                debug.update(
                    {
                        "fallback_reason": "validation_error",
                        "tool_validation": "failed",
                        "selected_tool": spec.tool_id,
                        "missing_fields": [field],
                    }
                )
                record_event(
                    "assistant.tool.validation",
                    {
                        "tool_id": spec.tool_id,
                        "status": "failed",
                        "missing_field_count": 1,
                    },
                )
                new_messages.append(
                    ToolMessage(
                        content=f"Parametre dogrulamasi basarisiz: {validation_error}",
                        tool_call_id=call["id"],
                    )
                )
                new_messages.append(
                    AIMessage(
                        content=(
                            "Bu araci calistirmak icin net bilgi eksik veya hatali: "
                            f"{validation_error}. Lutfen bu bilgiyi tek mesajda belirtin."
                        )
                    )
                )
                return {"messages": new_messages, "debug": debug}

            debug.update(
                {
                    "tool_validation": "ok",
                    "selected_tool": spec.tool_id,
                    "selected_tool_hitl": spec.hitl,
                }
            )
            record_event(
                "assistant.tool.validation",
                {"tool_id": spec.tool_id, "status": "ok", "hitl": spec.hitl},
            )

            if spec.hitl:
                assert validated_args is not None
                ozet = compose_proposed_action_ozet(spec.tool_id, validated_args)
                debug["proposed_action_tool_id"] = spec.tool_id
                record_event(
                    "assistant.proposed_action.created",
                    {"tool_id": spec.tool_id, "role": rol or "bilinmiyor"},
                )
                return {
                    "proposed_action": {
                        "tool_id": spec.tool_id,
                        "params": validated_args,
                        "ozet": ozet,
                    },
                    "messages": [
                        ToolMessage(
                            content=f"[HITL ASKIDA] {spec.tool_id} onay bekliyor.",
                            tool_call_id=call["id"],
                        ),
                        AIMessage(content=f"Islem yapilmadi; onay bekliyor. {ozet}"),
                    ],
                    "debug": debug,
                }

            try:
                assert spec.executor is not None
                assert validated_args is not None
                if spec.requires_runtime:
                    sonuc = await spec.executor(
                        runtime_context=runtime_context,
                        **validated_args,
                    )
                else:
                    sonuc = await spec.executor(**validated_args)
                content = json.dumps(sonuc, ensure_ascii=False, default=str)
            except Exception as exc:  # noqa: BLE001 - safe tool boundary
                log.warning("Tool '%s' hatasi: %s", spec.tool_id, exc)
                debug.update(
                    {
                        "fallback_reason": "tool_execution_error",
                        "selected_tool": spec.tool_id,
                    }
                )
                record_event(
                    "assistant.tool.fallback",
                    {
                        "tool_id": spec.tool_id,
                        "fallback_reason": "tool_execution_error",
                    },
                )
                new_messages.append(
                    ToolMessage(
                        content="Read-only arac calisirken hata olustu.",
                        tool_call_id=call["id"],
                    )
                )
                new_messages.append(
                    AIMessage(
                        content=(
                            f"'{spec.tool_id}' sorgusu calisirken hata olustu. "
                            "Parametreleri kontrol edip tekrar deneyin."
                        )
                    )
                )
                return {"messages": new_messages, "debug": debug}

            new_messages.append(ToolMessage(content=content, tool_call_id=call["id"]))
            record_event(
                "assistant.tool.executed",
                {"tool_id": spec.tool_id, "status": "ok", "hitl": False},
            )

        return {"messages": new_messages, "debug": debug}

    return tool_dispatcher_node


def _fallback_tool_response(
    call: dict[str, Any],
    debug: dict[str, Any],
    *,
    fallback_reason: str,
    user_message: str,
    tool_id: str | None = None,
) -> dict[str, Any]:
    """Return a consistent terminal fallback for invalid tool selections."""
    debug.update(
        {
            "fallback_reason": fallback_reason,
            "selected_tool": tool_id or call["name"],
        }
    )
    record_event(
        "assistant.tool.fallback",
        {"tool_id": tool_id or call["name"], "fallback_reason": fallback_reason},
    )
    return {
        "messages": [
            ToolMessage(
                content=f"Arac cagrisi reddedildi: {fallback_reason}",
                tool_call_id=call["id"],
            ),
            AIMessage(content=user_message),
        ],
        "debug": debug,
    }


def _validation_field(validation_error: str) -> str:
    return validation_error.split(":", 1)[0].strip() or "parametre"


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
    """HITL and deterministic fallbacks end; read-only results return to LLM."""
    if state.get("proposed_action"):
        return "end"
    if (state.get("debug") or {}).get("fallback_reason"):
        return "end"
    return "llm"
