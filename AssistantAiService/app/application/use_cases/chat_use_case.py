"""Chat use case: graph.ainvoke wrapper.

Sorumluluk:
- Frontend (ya da BackendProje proxy) tarafindan gelen ChatRequest'i graph
  state'ine cevirir.
- `thread_id = kullanici_id:session_id` ile checkpointer'in dogru thread'i
  hedeflemesini saglar.
- Graph'in dondugu final state'ten son AIMessage'in icerigini ve varsa
  proposed_action'i ChatResponse'a paketler.

Test'lerde graph fake LLM ile insa edilir; UseCase'in icinde framework ozel
mantik yoktur, dolayisiyla yalniz UseCase'i ayrica test etmek gerekmez —
test_chat.py end-to-end TestClient ile cagiri test eder.
"""

from __future__ import annotations

import logging
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage

from app.api.v1.schemas import ChatRequest, ChatResponse, ProposedAction

log = logging.getLogger(__name__)


class ChatUseCase:
    def __init__(self, graph) -> None:
        self._graph = graph

    async def execute(self, request: ChatRequest) -> ChatResponse:
        kullanici_id = request.user_context.kullanici_id
        session_id = request.session_id or uuid4().hex
        thread_id = f"{kullanici_id}:{session_id}"

        config: dict = {"configurable": {"thread_id": thread_id}}

        input_state = {
            "messages": [HumanMessage(content=request.soru)],
            "user_context": request.user_context.model_dump(),
            "proposed_action": None,
            "debug": {},
        }

        final_state = await self._graph.ainvoke(input_state, config=config)

        cevap = _son_ai_metni(final_state.get("messages") or [])

        proposed_raw = final_state.get("proposed_action")
        proposed_action = (
            ProposedAction.model_validate(proposed_raw) if proposed_raw else None
        )
        if proposed_action is not None:
            lower = cevap.lower()
            if "onay bekliyor" not in lower and "islem yapilmadi" not in lower:
                cevap = f"{cevap}\n\nIslem yapilmadi; onay bekliyor."

        return ChatResponse(
            cevap=cevap,
            session_id=session_id,
            proposed_action=proposed_action,
            debug=final_state.get("debug") or None,
        )


def _son_ai_metni(messages: list) -> str:
    """Mesaj geçmişinin sonundan ilk AI mesajini ve metnini çek.

    Tool çağrısı varsa içerik boş olabilir; o durumda HITL askıda mesajını
    kullanıcıya nazikçe bildiren bir fallback metin döneriz.
    """
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            text = (msg.content or "").strip()
            if text:
                return text
            # Boş içerik ama tool_calls var: HITL askıda kelimelerini ima eden cevap
            if getattr(msg, "tool_calls", None):
                return (
                    "Bir aksiyon onerdim. Lutfen yukaridaki ozeti gozden "
                    "gecirip onaylayin veya reddedin."
                )
    return "Su an cevap olusturulamadi."
