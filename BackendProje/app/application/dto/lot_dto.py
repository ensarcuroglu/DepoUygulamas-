"""
Lot veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.lot import Lot


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class LotOlusturRequestDTO(BaseModel):
    urun_id: int = Field(..., gt=0, description="Ürün ID")
    lot_no: Optional[str] = Field(None, max_length=100)
    parti_no: Optional[str] = Field(None, max_length=100)
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    aciklama: str = Field(default="", max_length=2000)


class LotGuncelleRequestDTO(BaseModel):
    lot_no: Optional[str] = Field(None, max_length=100)
    parti_no: Optional[str] = Field(None, max_length=100)
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    aciklama: Optional[str] = Field(None, max_length=2000)
    aktif: Optional[bool] = None


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class LotResponseDTO(BaseModel):
    id: int
    urun_id: int
    lot_no: Optional[str] = None
    parti_no: Optional[str] = None
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    aciklama: str
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Lot) -> "LotResponseDTO":
        return cls(
            id=entity.id,
            urun_id=entity.urun_id,
            lot_no=entity.lot_no,
            parti_no=entity.parti_no,
            uretim_tarihi=entity.uretim_tarihi,
            son_kullanma_tarihi=entity.son_kullanma_tarihi,
            aciklama=entity.aciklama,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
