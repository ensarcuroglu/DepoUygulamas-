"""LangGraph state schema for the depo asistani.

LangGraph state'i bir TypedDict'tir; her node, donus degerinde **degisecek**
anahtarlari icerir (full state'i kopyalamak gerekmez). `messages` icin
`add_messages` reducer'i LLM/araç mesajlarini biriktirir; diger alanlar
override semantigiyle yenilenir.
"""

from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class UserContextSnapshot(TypedDict, total=False):
    """Backend'in JWT'den cikarip ilettigi serialize edilmis baglam.

    `total=False` cunku Faz 2 PoC'sinde bazi alanlar opsiyonel; Faz 3'te
    aktif_gorev_id zorunlu hale getirilebilir.
    """

    kullanici_id: int
    rol: str
    aktif_gorev_id: int | None
    aktif_ekran: str | None
    izinli_tool_idleri: list[str]


class ProposedActionSnapshot(TypedDict):
    """HITL tool tetiklendiginde dispatcher'in graph state'ine yazdigi paket."""

    tool_id: str
    params: dict[str, Any]
    ozet: str | None


class AssistantState(TypedDict, total=False):
    """Per-thread graph state.

    Key invariant'lar:
    - `proposed_action` HITL kestiriminde set edilir; varsa graph END'e gider.
    - `messages` reducer'i `add_messages` oldugu icin liste override edilmez;
      sadece eklenir. Eski mesajlari silmek istiyorsak ozel reducer gerekir.
    """

    messages: Annotated[list[BaseMessage], add_messages]
    user_context: UserContextSnapshot
    proposed_action: ProposedActionSnapshot | None
    debug: dict[str, Any]
