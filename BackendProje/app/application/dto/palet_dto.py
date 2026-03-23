"""
Palet veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.core.entities.palet import Palet


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class PaletOlusturRequestDTO(BaseModel):
    lot_id: int = Field(..., gt=0, description="LOT ID")
    raf_id: Optional[int] = Field(None, gt=0, description="Raf ID")
    palet_no: str = Field(..., min_length=1, max_length=100)
    koli_adedi: int = Field(..., gt=0, description="Koli adedi pozitif olmalı")
    palet_kg: Optional[float] = Field(None, ge=0)
    vardiya: Optional[str] = Field(None, max_length=50)


class PaletGuncelleRequestDTO(BaseModel):
    raf_id: Optional[int] = Field(None, gt=0)
    koli_adedi: Optional[int] = Field(None, gt=0)
    palet_kg: Optional[float] = Field(None, ge=0)
    vardiya: Optional[str] = Field(None, max_length=50)
    aktif: Optional[bool] = None


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class PaletResponseDTO(BaseModel):
    id: int
    lot_id: int
    raf_id: Optional[int] = None
    palet_no: str
    koli_adedi: int
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None
    tarih: datetime
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Palet) -> "PaletResponseDTO":
        return cls(
            id=entity.id,
            lot_id=entity.lot_id,
            raf_id=entity.raf_id,
            palet_no=entity.palet_no,
            koli_adedi=entity.koli_adedi,
            palet_kg=entity.palet_kg,
            vardiya=entity.vardiya,
            tarih=entity.tarih,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
