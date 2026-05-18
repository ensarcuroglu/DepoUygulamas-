"""DI - AssistantAiService entegrasyonu."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.application.services.asistan_tool_registry import (
    AsistanToolRegistry,
    get_tool_registry,
)
from app.application.use_cases.asistan_use_cases import (
    AsistanChatProxyUseCase,
    AsistanTaslakListeleUseCase,
    AsistanTaslakOnaylaUseCase,
    AsistanTaslakReddetUseCase,
)
from app.core.config import Settings, get_settings
from app.infrastructure.persistence.repositories import (
    SqlAlchemyAsistanAksiyonTaslagiRepository,
)
from app.infrastructure.services.assistant_ai_client import AssistantAiClient
from database import get_db


def get_asistan_aksiyon_taslagi_repo(db: Session = Depends(get_db)):
    return SqlAlchemyAsistanAksiyonTaslagiRepository(db)


def get_asistan_tool_registry() -> AsistanToolRegistry:
    return get_tool_registry()


def get_assistant_ai_client(settings: Settings = Depends(get_settings)) -> AssistantAiClient:
    return AssistantAiClient(settings)


def get_asistan_chat_proxy_uc(
    db: Session = Depends(get_db),
    registry: AsistanToolRegistry = Depends(get_asistan_tool_registry),
    repo=Depends(get_asistan_aksiyon_taslagi_repo),
    client: AssistantAiClient = Depends(get_assistant_ai_client),
    settings: Settings = Depends(get_settings),
) -> AsistanChatProxyUseCase:
    return AsistanChatProxyUseCase(
        tool_registry=registry,
        taslak_repo=repo,
        client=client,
        db=db,
        draft_ttl_seconds=settings.asistan_draft_ttl_seconds,
    )


def get_asistan_taslak_listele_uc(
    repo=Depends(get_asistan_aksiyon_taslagi_repo),
) -> AsistanTaslakListeleUseCase:
    return AsistanTaslakListeleUseCase(repo)


def get_asistan_taslak_onayla_uc(
    db: Session = Depends(get_db),
    registry: AsistanToolRegistry = Depends(get_asistan_tool_registry),
    repo=Depends(get_asistan_aksiyon_taslagi_repo),
) -> AsistanTaslakOnaylaUseCase:
    return AsistanTaslakOnaylaUseCase(
        tool_registry=registry,
        taslak_repo=repo,
        db=db,
    )


def get_asistan_taslak_reddet_uc(
    db: Session = Depends(get_db),
    repo=Depends(get_asistan_aksiyon_taslagi_repo),
) -> AsistanTaslakReddetUseCase:
    return AsistanTaslakReddetUseCase(
        taslak_repo=repo,
        db=db,
    )
