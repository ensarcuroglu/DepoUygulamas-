"""Shared API schemas for AssistantAiService."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class UserContext(BaseModel):
    """Backend-supplied authenticated user context."""

    kullanici_id: int
    rol: str
    aktif_gorev_id: Optional[int] = None
    aktif_ekran: Optional[str] = None
    izinli_tool_idleri: list[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    """Backend -> AssistantAiService chat request."""

    soru: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, max_length=128)
    user_context: UserContext


class ProposedAction(BaseModel):
    """HITL action proposal returned to BackendProje for draft creation."""

    tool_id: str = Field(..., max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)
    ozet: Optional[str] = Field(None, max_length=500)


class ChatResponse(BaseModel):
    """AssistantAiService -> BackendProje chat response."""

    cevap: str
    session_id: Optional[str] = None
    proposed_action: Optional[ProposedAction] = None
    debug: Optional[dict[str, Any]] = None
