"""AGV servisinden gelen callback'leri işleyen router.

Auth: X-Internal-Api-Key header (JWT YOK).
Endpoint'ler:
- POST /api/agv-callbacks/gorev-tamamlandi — robot görevi bitirdi.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.v1.internal_auth import internal_api_key_verify
from app.application.dto.agv_callback_dto import (
    AgvCallbackResponseDTO,
    AgvGorevTamamlamaCallbackDTO,
)
from app.application.use_cases.agv_yerlestirme_tamamla_use_case import (
    AgvYerlestirmeTamamlaUseCase,
)
from app.infrastructure.di.container import (
    get_agv_kullanici_id,
    get_agv_yerlestirme_tamamla_uc,
)

router = APIRouter(
    prefix="/api/agv-callbacks",
    tags=["AGV Callback"],
    dependencies=[Depends(internal_api_key_verify)],
)


@router.post(
    "/gorev-tamamlandi",
    response_model=AgvCallbackResponseDTO,
)
def gorev_tamamlandi(
    dto: AgvGorevTamamlamaCallbackDTO,
    agv_user_id: int = Depends(get_agv_kullanici_id),
    uc: AgvYerlestirmeTamamlaUseCase = Depends(get_agv_yerlestirme_tamamla_uc),
) -> AgvCallbackResponseDTO:
    """AGV bir yerleştirme görevini bitirdi → WMS'te kapat (idempotent)."""
    return uc.execute(dto, agv_kullanici_id=agv_user_id)
