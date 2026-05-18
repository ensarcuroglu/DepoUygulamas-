"""Chat endpoint for AssistantAiService.

LangGraph agent loop'u arkada baglar. Tek HTTP yuzeyi `/api/asistan/chat`;
fiili graph compile etmek `main.py` lifespan'inde yapilir ve `app.state.graph`
uzerinde paylasilir. Dep override edilerek test'lerde fake graph enjekte edilir.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.api.v1.schemas import ChatRequest, ChatResponse
from app.application.use_cases.chat_use_case import ChatUseCase

router = APIRouter(prefix="/api/asistan", tags=["Depo Asistani"])


def get_graph(request: Request):
    """Lifespan tarafindan `app.state.graph` uzerine konan compiled graph."""
    return request.app.state.graph


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    graph=Depends(get_graph),
) -> ChatResponse:
    use_case = ChatUseCase(graph)
    return await use_case.execute(request)
