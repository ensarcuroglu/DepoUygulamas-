from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.application.dto import TalepTahminResponseDTO, TalepTahminUrunOzetDTO
from app.application.use_cases import (
    TalepTahminUrunleriListeleUseCase,
    TalepTahminiGetirUseCase,
)
from app.core.auth import require_role
from app.infrastructure.di.container import (
    get_talep_tahmin_urunleri_listele_uc,
    get_talep_tahmini_getir_uc,
)
from limiter import limiter
from models import Kullanici


router = APIRouter(prefix="/api/talep-tahmini", tags=["Talep Tahmini"])


@router.get("/urunler", response_model=list[TalepTahminUrunOzetDTO])
@limiter.limit("60/minute")
def tahmin_urunleri_listele(
    request: Request,
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None, max_length=100),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: TalepTahminUrunleriListeleUseCase = Depends(get_talep_tahmin_urunleri_listele_uc),
):
    return uc.execute(limit=limit, search=search)


@router.get("/urunler/{urun_id}", response_model=TalepTahminResponseDTO)
@limiter.limit("60/minute")
def urun_talep_tahmini_getir(
    request: Request,
    urun_id: int,
    tahmin_gun: int = Query(7),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: TalepTahminiGetirUseCase = Depends(get_talep_tahmini_getir_uc),
):
    if tahmin_gun not in {7, 14, 30, 90}:
        raise HTTPException(status_code=422, detail="tahmin_gun 7, 14, 30 veya 90 olmalidir.")
    return uc.execute(urun_id=urun_id, tahmin_gun=tahmin_gun)
