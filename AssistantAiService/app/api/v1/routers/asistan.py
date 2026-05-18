"""Chat endpoint for AssistantAiService.

This router exposes the BackendProje contract now, while the LangGraph agent
core is still introduced incrementally. It never performs DB writes and it does
not create HITL actions until real tool orchestration is registered.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter

from app.api.v1.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/asistan", tags=["Depo Asistani"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or uuid4().hex
    return ChatResponse(
        cevap=(
            "Depo Asistani baglantisi hazir. Su anda guvenli sohbet modundayim; "
            "aksiyon onermek icin tool orkestrasyonu etkinlestirilmedi."
        ),
        session_id=session_id,
        proposed_action=None,
        debug={
            "mode": "contract_ready",
            "rol": request.user_context.rol,
            "izinli_tool_sayisi": len(request.user_context.izinli_tool_idleri),
        },
    )
