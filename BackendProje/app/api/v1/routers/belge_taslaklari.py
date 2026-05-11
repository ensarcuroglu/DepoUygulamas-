"""Belge taslagi endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.api.v1.internal_auth import internal_api_key_verify
from app.application.dto import (
    BelgeTaslagiOlusturRequestDTO,
    BelgeTaslagiOnaylaRequestDTO,
    BelgeTaslagiReddetRequestDTO,
    BelgeTaslagiResponseDTO,
)
from app.application.use_cases import (
    BelgeTaslagiGetirUseCase,
    BelgeTaslagiIncelemeKuyruguUseCase,
    BelgeTaslagiListeleUseCase,
    BelgeTaslagiOlusturUseCase,
    BelgeTaslagiOnaylaUseCase,
    BelgeTaslagiReddetUseCase,
)
from app.core.auth import require_role
from app.core.exceptions import YetkisizIslemError
from app.core.idempotency import idempotency_kaydet, idempotency_kontrol
from app.infrastructure.di.container import (
    get_belge_taslagi_getir_uc,
    get_belge_taslagi_inceleme_kuyrugu_uc,
    get_belge_taslagi_listele_uc,
    get_belge_taslagi_olustur_uc,
    get_belge_taslagi_onayla_uc,
    get_belge_taslagi_reddet_uc,
)
from database import get_db
from models import Kullanici


router = APIRouter(prefix="/api/belge-taslaklari", tags=["Belge Taslaklari"])


@router.post(
    "/",
    response_model=BelgeTaslagiResponseDTO,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(internal_api_key_verify)],
)
def belge_taslagi_olustur_callback(
    dto: BelgeTaslagiOlusturRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    uc: BelgeTaslagiOlusturUseCase = Depends(get_belge_taslagi_olustur_uc),
):
    """DocAiService internal callback endpoint'i."""
    endpoint = "belge_taslaklari_callback"
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, endpoint)
        if cached is not None:
            return cached

    sonuc = uc.execute(dto)
    if idempotency_key:
        idempotency_kaydet(db, idempotency_key, endpoint, sonuc.model_dump(mode="json"))
    return sonuc


@router.get("/", response_model=list[BelgeTaslagiResponseDTO])
def belge_taslaklari_listele(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    durum: Optional[str] = Query(None),
    depo_id: Optional[int] = Query(None),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: BelgeTaslagiListeleUseCase = Depends(get_belge_taslagi_listele_uc),
):
    if current_user.rol == "depocu":
        kullanici_depo_id = getattr(current_user, "depo_id", None)
        if depo_id and kullanici_depo_id and depo_id != kullanici_depo_id:
            raise YetkisizIslemError("Bu depo icin belge taslagi goruntuleme yetkiniz yok.")
        depo_id = kullanici_depo_id or depo_id
    return uc.execute(skip=skip, limit=limit, durum=durum, depo_id=depo_id)


@router.get("/inceleme-kuyrugu", response_model=list[BelgeTaslagiResponseDTO])
def belge_taslaklari_inceleme_kuyrugu(
    skip: int = 0,
    limit: int = Query(default=100, le=500),
    depo_id: Optional[int] = Query(None),
    max_confidence: float = Query(default=0.6, gt=0.0, le=1.0),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
    uc: BelgeTaslagiIncelemeKuyruguUseCase = Depends(
        get_belge_taslagi_inceleme_kuyrugu_uc
    ),
):
    return uc.execute(
        skip=skip,
        limit=limit,
        depo_id=depo_id,
        max_confidence=max_confidence,
    )


@router.get("/{taslak_id}", response_model=BelgeTaslagiResponseDTO)
def belge_taslagi_detay(
    taslak_id: int,
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    uc: BelgeTaslagiGetirUseCase = Depends(get_belge_taslagi_getir_uc),
):
    sonuc = uc.execute(taslak_id)
    if current_user.rol == "depocu":
        kullanici_depo_id = getattr(current_user, "depo_id", None)
        if kullanici_depo_id and sonuc.depo_id != kullanici_depo_id:
            raise YetkisizIslemError("Bu belge taslagina erisim yetkiniz yok.")
    return sonuc


@router.post("/{taslak_id}/onayla", response_model=BelgeTaslagiResponseDTO)
def belge_taslagi_onayla(
    taslak_id: int,
    dto: BelgeTaslagiOnaylaRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    db: Session = Depends(get_db),
    uc: BelgeTaslagiOnaylaUseCase = Depends(get_belge_taslagi_onayla_uc),
):
    endpoint = f"belge_taslagi_onayla:{taslak_id}"
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, endpoint)
        if cached is not None:
            return cached

    sonuc = uc.execute(taslak_id, dto, kullanici_id=current_user.id)
    if idempotency_key:
        idempotency_kaydet(db, idempotency_key, endpoint, sonuc.model_dump(mode="json"))
    return sonuc


@router.post("/{taslak_id}/reddet", response_model=BelgeTaslagiResponseDTO)
def belge_taslagi_reddet(
    taslak_id: int,
    dto: BelgeTaslagiReddetRequestDTO,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    db: Session = Depends(get_db),
    uc: BelgeTaslagiReddetUseCase = Depends(get_belge_taslagi_reddet_uc),
):
    endpoint = f"belge_taslagi_reddet:{taslak_id}"
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, endpoint)
        if cached is not None:
            return cached

    sonuc = uc.execute(taslak_id, dto, kullanici_id=current_user.id)
    if idempotency_key:
        idempotency_kaydet(db, idempotency_key, endpoint, sonuc.model_dump(mode="json"))
    return sonuc
