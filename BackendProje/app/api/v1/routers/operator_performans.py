"""Operatör Performans (LMS) — okuma uçları.

Roller:
  admin, lojistik     → tüm operatörlerin metrikleri + leaderboard
  depocu              → sadece kendi metrikleri (`/me`, `/kullanici/{kendi_id}`)
                        + leaderboard (gamification)
  goruntuleyen        → tüm metrikleri okur (read-only rol)
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.application.dto import (
    KendiPerformansOzetDTO,
    LeaderboardResponseDTO,
    OperatorMetrikItemDTO,
    OperatorOzetListResponseDTO,
)
from app.application.use_cases import OperatorPerformansSorguUseCase
from app.core.auth import get_current_user, require_role
from app.infrastructure.di.container import get_operator_performans_sorgu_uc
from limiter import limiter
from models import Kullanici


router = APIRouter(
    prefix="/api/operator-performans",
    tags=["Operatör Performans"],
)


@router.get("/ozet", response_model=OperatorOzetListResponseDTO)
@limiter.limit("60/minute")
def operator_ozet_listele(
    request: Request,
    baslangic: Optional[date] = Query(None, description="Başlangıç tarihi (dahil)"),
    bitis: Optional[date] = Query(None, description="Bitiş tarihi (dahil)"),
    depo_id: Optional[int] = Query(None, ge=1),
    kullanici_id: Optional[int] = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    current_user: Kullanici = Depends(
        require_role("admin", "lojistik", "goruntuleyen")
    ),
    uc: OperatorPerformansSorguUseCase = Depends(get_operator_performans_sorgu_uc),
):
    """Tarih aralığı + opsiyonel depo/kullanıcı filtresiyle vardiya KPI listesi."""
    if baslangic and bitis and baslangic > bitis:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="baslangic, bitis tarihinden sonra olamaz.",
        )
    return uc.ozet_getir(
        baslangic=baslangic,
        bitis=bitis,
        depo_id=depo_id,
        kullanici_id=kullanici_id,
        skip=skip,
        limit=limit,
    )


@router.get("/leaderboard", response_model=LeaderboardResponseDTO)
@limiter.limit("60/minute")
def leaderboard_getir(
    request: Request,
    vardiya_tarihi: Optional[date] = Query(
        None, description="Boş bırakılırsa bugün"
    ),
    depo_id: Optional[int] = Query(None, ge=1),
    limit: int = Query(10, ge=1, le=50),
    current_user: Kullanici = Depends(
        require_role("admin", "lojistik", "depocu", "goruntuleyen")
    ),
    uc: OperatorPerformansSorguUseCase = Depends(get_operator_performans_sorgu_uc),
):
    """Tek günlük UPH sıralaması — tüm rollere açık (gamification)."""
    return uc.leaderboard_getir(
        vardiya_tarihi=vardiya_tarihi,
        depo_id=depo_id,
        limit=limit,
    )


@router.get("/me", response_model=KendiPerformansOzetDTO)
@limiter.limit("60/minute")
def kendi_performansim(
    request: Request,
    gun_sayisi: int = Query(7, ge=1, le=30),
    current_user: Kullanici = Depends(get_current_user),
    uc: OperatorPerformansSorguUseCase = Depends(get_operator_performans_sorgu_uc),
):
    """Oturum kullanıcısının son N günlük özeti + bugünkü kayıt."""
    return uc.kendi_metriklerim(
        kullanici_id=current_user.id, gun_sayisi=gun_sayisi
    )


@router.get(
    "/kullanici/{kullanici_id}",
    response_model=list[OperatorMetrikItemDTO],
)
@limiter.limit("60/minute")
def kullanici_detay_getir(
    request: Request,
    kullanici_id: int,
    baslangic: Optional[date] = Query(None),
    bitis: Optional[date] = Query(None),
    limit: int = Query(90, ge=1, le=365),
    current_user: Kullanici = Depends(get_current_user),
    uc: OperatorPerformansSorguUseCase = Depends(get_operator_performans_sorgu_uc),
):
    """Kullanıcı bazlı vardiya geçmişi.

    `depocu` rolü yalnızca kendi id'siyle çağırabilir; admin/lojistik/goruntuleyen
    serbestçe sorgulayabilir.
    """
    rol = (current_user.rol or "").lower()
    if rol not in {"admin", "lojistik", "goruntuleyen"} and current_user.id != kullanici_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Başka bir kullanıcının metriklerini görüntüleme yetkiniz yok.",
        )
    if baslangic and bitis and baslangic > bitis:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="baslangic, bitis tarihinden sonra olamaz.",
        )
    return uc.kullanici_detay_getir(
        kullanici_id=kullanici_id,
        baslangic=baslangic,
        bitis=bitis,
        limit=limit,
    )
