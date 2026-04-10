"""
Marka veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.marka import Marka


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class MarkaOlusturRequestDTO(BaseModel):
    isim: str = Field(..., min_length=1, max_length=200, description="Marka adı")
    aciklama: str = Field(default="", max_length=2000)

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Marka ismi boş olamaz.")
        return v.strip()


class MarkaGuncelleRequestDTO(BaseModel):
    isim: Optional[str] = Field(None, min_length=1, max_length=200)
    aciklama: Optional[str] = Field(None, max_length=2000)
    aktif: Optional[bool] = None

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Marka ismi boş olamaz.")
        return v.strip() if v else v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class MarkaResponseDTO(BaseModel):
    id: int
    isim: str
    aciklama: str
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Marka) -> "MarkaResponseDTO":

        if entity.id is None:
            raise ValueError("MarkaResponseDTO oluşturulamadı: entity.id boş olamaz.")

        return cls(
            id=entity.id,
            isim=entity.isim,
            aciklama=entity.aciklama,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
