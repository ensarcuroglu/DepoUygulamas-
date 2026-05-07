"""Görev push/response DTO'ları (BackendProje ↔ AgvSimService)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class GorevPushRequestDTO(BaseModel):
    """BackendProje → AgvSimService — yeni görev push'u."""

    wms_gorev_id: int
    wms_gorev_tipi: Literal["Yerlestirme", "Toplama"] = "Yerlestirme"
    depo_id: Optional[int] = None
    kaynak_raf_id: int
    hedef_raf_id: int
    palet_id: Optional[int] = None
    oncelik: int = Field(default=5, ge=1, le=5)


class GorevPushResponseDTO(BaseModel):
    kabul_edildi: bool
    agv_gorev_id: str
    kuyruk_uzunlugu: int


class GorevTamamlamaCallbackDTO(BaseModel):
    """AgvSimService → BackendProje (Faz 3'te kullanılacak şablon)."""

    wms_gorev_id: int
    wms_gorev_tipi: Literal["Yerlestirme", "Toplama"]
    robot_id: str
    gerceklesen_raf_id: int
    sim_baslama_tick: Optional[int] = None
    sim_tamamlanma_tick: Optional[int] = None
    rota_uzunlugu: Optional[int] = None
