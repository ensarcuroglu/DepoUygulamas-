"""
Sistem Logları API Router — Clean Architecture (Thin Controller).
"""

from fastapi import APIRouter, Depends, Query, Request
from typing import List

from auth import get_current_user, require_role
from models import Kullanici
from limiter import limiter

from app.infrastructure.di.container import (
    get_sistem_log_listele_uc,
    get_sistem_log_olustur_uc,
)
from app.application.dto.sistem_log_dto import (
    SistemLogOlusturRequestDTO,
    SistemLogResponseDTO,
)
from app.application.use_cases.sistem_log_use_cases import (
    SistemLogListeleUseCase,
    SistemLogOlusturUseCase,
)

router = APIRouter(prefix="/api/sistem-loglari", tags=["Sistem Logları"])


@router.get("/", response_model=List[SistemLogResponseDTO])
@limiter.limit("100/minute")
def get_loglar(
    request: Request,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: Kullanici = Depends(require_role("admin")),
    uc: SistemLogListeleUseCase = Depends(get_sistem_log_listele_uc),
):
    return uc.execute(skip=skip, limit=limit)


@router.post("/", response_model=SistemLogResponseDTO)
@limiter.limit("50/minute")
def create_log(
    request: Request,
    data: SistemLogOlusturRequestDTO,
    current_user: Kullanici = Depends(get_current_user),
    uc: SistemLogOlusturUseCase = Depends(get_sistem_log_olustur_uc),
):
    return uc.execute(data, kullanici_id=current_user.id)
