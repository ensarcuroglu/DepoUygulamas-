"""Mal kabul belge upload endpoints."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Header, UploadFile, status
from sqlalchemy.orm import Session

from app.application.dto import BelgeTaslagiOlusturRequestDTO, BelgeTaslagiResponseDTO
from app.application.use_cases import BelgeTaslagiOlusturUseCase
from app.core.auth import require_role
from app.core.config import FeatureFlags, get_settings
from app.core.exceptions import GecersizIslemError, YetkisizIslemError
from app.core.idempotency import idempotency_kaydet, idempotency_kontrol
from app.infrastructure.di.container import get_belge_taslagi_olustur_uc, get_doc_ai_client
from app.infrastructure.services.doc_ai_client import DocAiClient
from database import get_db
from models import Kullanici


router = APIRouter(prefix="/api/mal-kabul", tags=["Mal Kabul"])

BACKEND_ROOT = Path(__file__).resolve().parents[4]
UPLOAD_ROOT = BACKEND_ROOT / "uploads" / "belge_taslaklari"


def _safe_filename(filename: Optional[str]) -> str:
    name = Path(filename or "belge").name
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("._")
    return cleaned or "belge"


def _extract_confidence(payload: dict[str, Any]) -> float:
    taslak = payload.get("taslak") if isinstance(payload.get("taslak"), dict) else payload
    value = payload.get("confidence_skoru") or payload.get("confidence_score")
    if value is None and isinstance(taslak, dict):
        value = taslak.get("confidence_score")
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(confidence, 1.0))


def _store_upload(content: bytes, filename: Optional[str]) -> str:
    today_dir = UPLOAD_ROOT / datetime.utcnow().strftime("%Y%m%d")
    today_dir.mkdir(parents=True, exist_ok=True)
    stored = today_dir / f"{uuid4().hex}_{_safe_filename(filename)}"
    stored.write_bytes(content)
    return str(stored.relative_to(BACKEND_ROOT))


@router.post(
    "/belge-yukle",
    response_model=BelgeTaslagiResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
def mal_kabul_belge_yukle(
    depo_id: int = Form(..., gt=0),
    file: UploadFile = File(...),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu")),
    db: Session = Depends(get_db),
    doc_ai_client: DocAiClient = Depends(get_doc_ai_client),
    olustur_uc: BelgeTaslagiOlusturUseCase = Depends(get_belge_taslagi_olustur_uc),
):
    """Belgeyi DocAiService'e gonderir ve WMS'te belge taslagi olusturur."""
    flags = FeatureFlags.from_settings(get_settings())
    if not flags.doc_ai_aktif_mi(depo_id):
        raise YetkisizIslemError("DocAi belge yukleme bu depo icin aktif degil.")

    if current_user.rol == "depocu" and getattr(current_user, "depo_id", None) != depo_id:
        raise YetkisizIslemError("Bu depo icin belge yukleme yetkiniz yok.")

    endpoint = f"mal_kabul_belge_yukle:{depo_id}"
    if idempotency_key:
        cached = idempotency_kontrol(db, idempotency_key, endpoint)
        if cached is not None:
            return cached

    content = file.file.read()
    if not content:
        raise GecersizIslemError("Yuklenen belge bos olamaz.")

    kaynak_dosya_yolu = _store_upload(content, file.filename)
    doc_ai_payload = doc_ai_client.extract_irsaliye(
        filename=file.filename or "belge",
        content_type=file.content_type,
        content=content,
        idempotency_key=idempotency_key,
    )

    dto = BelgeTaslagiOlusturRequestDTO(
        kaynak_dosya_yolu=kaynak_dosya_yolu,
        belge_tipi="IRSALIYE",
        ham_json=doc_ai_payload,
        confidence_skoru=_extract_confidence(doc_ai_payload),
        olusturan_kullanici_id=current_user.id,
        depo_id=depo_id,
    )
    sonuc = olustur_uc.execute(dto)
    if idempotency_key:
        idempotency_kaydet(db, idempotency_key, endpoint, sonuc.model_dump(mode="json"))
    return sonuc
