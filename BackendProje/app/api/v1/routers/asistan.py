"""Depo Asistani endpoint'leri.

Frontend `/api/asistan/*` uzerinden konusur; AssistantAiService'e proxy yapilir
ve LLM HITL tool secerse taslak veritabanina yazilir. Tum authoritative DB
mutasyonlari burada gerceklesir; AssistantAiService DB'ye dokunmaz.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.application.dto import (
    AsistanChatRequestDTO,
    AsistanChatResponseDTO,
    AsistanTaslakOnaylaRequestDTO,
    AsistanTaslakReddetRequestDTO,
    AsistanTaslakResponseDTO,
    AsistanToolListResponseDTO,
    AsistanToolMetaDTO,
)
from app.application.services.asistan_tool_registry import AsistanToolRegistry
from app.application.use_cases.asistan_use_cases import (
    AsistanChatProxyUseCase,
    AsistanTaslakListeleUseCase,
    AsistanTaslakOnaylaUseCase,
    AsistanTaslakReddetUseCase,
)
from app.core.auth import require_role
from app.core.config import Settings, get_settings
from app.infrastructure.di.container import (
    get_asistan_chat_proxy_uc,
    get_asistan_taslak_listele_uc,
    get_asistan_taslak_onayla_uc,
    get_asistan_taslak_reddet_uc,
    get_asistan_tool_registry,
)
from models import Kullanici


router = APIRouter(prefix="/api/asistan", tags=["Depo Asistani"])

# Rol seti: admin, lojistik, depocu. (Goruntuleyen su an dahil degil; istenirse
# Faz 3'te read-only chat icin acilabilir.)
_ASISTAN_ROLLERI = ("admin", "lojistik", "depocu")


def _ensure_enabled(settings: Settings = Depends(get_settings)) -> Settings:
    if not settings.feature_depo_asistani_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Depo Asistani ozelligi devre disi.",
        )
    return settings


@router.post("/chat", response_model=AsistanChatResponseDTO)
def asistan_chat(
    istek: AsistanChatRequestDTO,
    current_user: Kullanici = Depends(require_role(*_ASISTAN_ROLLERI)),
    uc: AsistanChatProxyUseCase = Depends(get_asistan_chat_proxy_uc),
    _settings: Settings = Depends(_ensure_enabled),
) -> AsistanChatResponseDTO:
    return uc.execute(istek, kullanici_id=current_user.id, rol=current_user.rol)


@router.get("/taslaklar", response_model=list[AsistanTaslakResponseDTO])
def asistan_taslaklar_listele(
    durum: Optional[str] = Query(None, max_length=30),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    sadece_kendim: bool = Query(True),
    current_user: Kullanici = Depends(require_role(*_ASISTAN_ROLLERI)),
    uc: AsistanTaslakListeleUseCase = Depends(get_asistan_taslak_listele_uc),
    _settings: Settings = Depends(_ensure_enabled),
) -> list[AsistanTaslakResponseDTO]:
    # depocu hicbir zaman baska kullanicinin taslagini goremez.
    if current_user.rol == "depocu" or sadece_kendim:
        kullanici_id = current_user.id
    else:
        kullanici_id = None
    return uc.execute(
        kullanici_id=kullanici_id,
        durum=durum,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/taslaklar/{taslak_id}/onayla",
    response_model=AsistanTaslakResponseDTO,
)
def asistan_taslak_onayla(
    taslak_id: int,
    istek: AsistanTaslakOnaylaRequestDTO,
    current_user: Kullanici = Depends(require_role(*_ASISTAN_ROLLERI)),
    uc: AsistanTaslakOnaylaUseCase = Depends(get_asistan_taslak_onayla_uc),
    _settings: Settings = Depends(_ensure_enabled),
) -> AsistanTaslakResponseDTO:
    return uc.execute(
        taslak_id=taslak_id,
        kullanici_id=current_user.id,
        rol=current_user.rol,
        istek=istek,
    )


@router.post(
    "/taslaklar/{taslak_id}/reddet",
    response_model=AsistanTaslakResponseDTO,
)
def asistan_taslak_reddet(
    taslak_id: int,
    istek: AsistanTaslakReddetRequestDTO,
    current_user: Kullanici = Depends(require_role(*_ASISTAN_ROLLERI)),
    uc: AsistanTaslakReddetUseCase = Depends(get_asistan_taslak_reddet_uc),
    _settings: Settings = Depends(_ensure_enabled),
) -> AsistanTaslakResponseDTO:
    return uc.execute(
        taslak_id=taslak_id,
        kullanici_id=current_user.id,
        istek=istek,
    )


@router.get("/tools", response_model=AsistanToolListResponseDTO)
def asistan_tools_listele(
    current_user: Kullanici = Depends(require_role(*_ASISTAN_ROLLERI)),
    registry: AsistanToolRegistry = Depends(get_asistan_tool_registry),
    _settings: Settings = Depends(_ensure_enabled),
) -> AsistanToolListResponseDTO:
    """Kullanicinin rolu icin erisilebilir tool'larin listesi."""
    specs = registry.list_for_role(current_user.rol)
    return AsistanToolListResponseDTO(
        tools=[
            AsistanToolMetaDTO(
                tool_id=spec.tool_id,
                aciklama=spec.aciklama,
                hitl=spec.hitl,
                rbac_roles=sorted(spec.rbac_roles),
            )
            for spec in specs
        ],
    )
