"""AssistantAiService entegrasyonu DTO'lari.

`/api/asistan/*` router'inin frontend ile ve AssistantAiService ile konustugu
veri tipleri burada toplanir. Authoritative yazimlar BackendProje icindeki use
case'ler tarafindan yapilir; AssistantAiService DB'ye dokunmaz.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Frontend <-> Backend
# ---------------------------------------------------------------------------

class AsistanChatRequestDTO(BaseModel):
    """Frontend'in /api/asistan/chat endpoint'ine yolladigi mesaj."""

    soru: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = Field(None, max_length=128)
    aktif_gorev_id: Optional[int] = Field(None, ge=1)
    aktif_ekran: Optional[str] = Field(None, max_length=120)


class ProposedActionDTO(BaseModel):
    """AssistantAiService LLM'inin onerdigi HITL aksiyon (henuz uygulanmamis)."""

    tool_id: str = Field(..., max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)
    ozet: Optional[str] = Field(None, max_length=500)


class AsistanTaslakResponseDTO(BaseModel):
    id: int
    kullanici_id: int
    rol: str
    tool_id: str
    payload_json: dict[str, Any]
    durum: str
    ozet: Optional[str] = None
    idempotency_key: str
    sonuc_json: Optional[dict[str, Any]] = None
    hata_mesaji: Optional[str] = None
    created_at: datetime
    expires_at: datetime
    executed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class AsistanChatResponseDTO(BaseModel):
    """Backend'in frontend'e dondugu sohbet cevabi."""

    soru: str
    cevap: str
    session_id: Optional[str] = None
    # LLM HITL tool secerse, taslak yaratilir ve burada dondurulur.
    taslak: Optional[AsistanTaslakResponseDTO] = None
    debug: Optional[dict[str, Any]] = None


class AsistanTaslakOnaylaRequestDTO(BaseModel):
    not_metni: Optional[str] = Field(None, max_length=500)


class AsistanTaslakReddetRequestDTO(BaseModel):
    sebep: Optional[str] = Field(None, max_length=500)


# ---------------------------------------------------------------------------
# Backend <-> AssistantAiService (upstream payload, internal)
# ---------------------------------------------------------------------------

class AsistanUserContextDTO(BaseModel):
    """Backend'in JWT'den cikarip AssistantAiService'e ilettigi bilgi paketi."""

    kullanici_id: int
    rol: str
    aktif_gorev_id: Optional[int] = None
    aktif_ekran: Optional[str] = None
    izinli_tool_idleri: list[str] = Field(default_factory=list)


class AsistanUpstreamChatRequestDTO(BaseModel):
    """Backend -> AssistantAiService chat istegi."""

    soru: str
    session_id: Optional[str] = None
    user_context: AsistanUserContextDTO


class AsistanUpstreamChatResponseDTO(BaseModel):
    """AssistantAiService -> Backend chat cevabi."""

    cevap: str
    session_id: Optional[str] = None
    # LLM tool secerse, draft burada doner; backend taslak tablosuna yazar.
    proposed_action: Optional[ProposedActionDTO] = None
    debug: Optional[dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Tool registry public meta (Faz 2/3 frontend listeleme icin opsiyonel)
# ---------------------------------------------------------------------------

class AsistanToolMetaDTO(BaseModel):
    tool_id: str
    aciklama: str
    hitl: bool
    rbac_roles: list[str]


class AsistanToolListResponseDTO(BaseModel):
    tools: list[AsistanToolMetaDTO]
