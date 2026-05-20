from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.application.dto import (
    BacktestOzetDTO,
    ParquetBacktestRequestDTO,
    ParquetBacktestSonucDTO,
    ParquetVeriSetiDTO,
    RiskliUrunDTO,
    TalepTahminResponseDTO,
    TalepTahminUrunOzetDTO,
)
from app.application.use_cases import (
    BacktestOzetGetirUseCase,
    ParquetBacktestUseCase,
    RiskliUrunlerListeleUseCase,
    TalepTahminUrunleriListeleUseCase,
    TalepTahminiGetirUseCase,
)
from app.core.auth import require_role
from app.infrastructure.di.container import (
    get_backtest_ozet_getir_uc,
    get_parquet_backtest_uc,
    get_riskli_urunler_listele_uc,
    get_talep_tahmin_urunleri_listele_uc,
    get_talep_tahmini_getir_uc,
)
from limiter import limiter
from models import Kullanici


router = APIRouter(prefix="/api/talep-tahmini", tags=["Talep Tahmini"])

_GECERLI_UFUKLAR = {7, 14, 30, 90}


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
    if tahmin_gun not in _GECERLI_UFUKLAR:
        raise HTTPException(status_code=422, detail="tahmin_gun 7, 14, 30 veya 90 olmalidir.")
    return uc.execute(urun_id=urun_id, tahmin_gun=tahmin_gun)


@router.get("/riskli-urunler", response_model=list[RiskliUrunDTO])
@limiter.limit("60/minute")
def riskli_urunler_listele(
    request: Request,
    tahmin_gun: int = Query(7),
    siniflandirma: str = Query(
        "kritik,dikkat",
        description="Virgulle ayrilmis risk seviyeleri (kritik, dikkat, yok).",
    ),
    limit: int = Query(50, ge=1, le=200),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: RiskliUrunlerListeleUseCase = Depends(get_riskli_urunler_listele_uc),
):
    if tahmin_gun not in _GECERLI_UFUKLAR:
        raise HTTPException(status_code=422, detail="tahmin_gun 7, 14, 30 veya 90 olmalidir.")
    seviyeler = tuple(
        s.strip()
        for s in siniflandirma.split(",")
        if s.strip() in {"kritik", "dikkat", "yok"}
    )
    if not seviyeler:
        seviyeler = ("kritik", "dikkat")
    return uc.execute(
        tahmin_gun=tahmin_gun,
        risk_seviyeleri=seviyeler,
        limit=limit,
    )


@router.get("/backtest-ozet", response_model=BacktestOzetDTO)
@limiter.limit("30/minute")
def backtest_ozet_getir(
    request: Request,
    tahmin_gun: int = Query(7),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: BacktestOzetGetirUseCase = Depends(get_backtest_ozet_getir_uc),
):
    if tahmin_gun not in _GECERLI_UFUKLAR:
        raise HTTPException(status_code=422, detail="tahmin_gun 7, 14, 30 veya 90 olmalidir.")
    return uc.execute(tahmin_gun=tahmin_gun)


@router.get("/backtest/veri-setleri", response_model=list[ParquetVeriSetiDTO])
@limiter.limit("30/minute")
def backtest_veri_setlerini_listele(
    request: Request,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: ParquetBacktestUseCase = Depends(get_parquet_backtest_uc),
):
    return uc.veri_setlerini_listele()


@router.post("/backtest/parquet", response_model=ParquetBacktestSonucDTO)
@limiter.limit("10/minute")
def backtest_parquet_calistir(
    request: Request,
    payload: ParquetBacktestRequestDTO,
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: ParquetBacktestUseCase = Depends(get_parquet_backtest_uc),
):
    if payload.tahmin_gun not in _GECERLI_UFUKLAR:
        raise HTTPException(status_code=422, detail="tahmin_gun 7, 14, 30 veya 90 olmalidir.")
    return uc.calistir(
        dosya=payload.dosya,
        tahmin_gun=payload.tahmin_gun,
        urun_id=payload.urun_id,
    )
