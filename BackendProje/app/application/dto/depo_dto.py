"""
Depo veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.depo import Depo


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class DepoOlusturRequestDTO(BaseModel):
    isim: str = Field(..., min_length=1, max_length=200, description="Depo adı")
    adres: str = Field(default="", max_length=500)
    aciklama: str = Field(default="", max_length=2000)

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Depo ismi boş olamaz.")
        return v.strip()


class DepoGuncelleRequestDTO(BaseModel):
    isim: Optional[str] = Field(None, min_length=1, max_length=200)
    adres: Optional[str] = Field(None, max_length=500)
    aciklama: Optional[str] = Field(None, max_length=2000)
    aktif: Optional[bool] = None

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Depo ismi boş olamaz.")
        return v.strip() if v else v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class DepoResponseDTO(BaseModel):
    id: int
    isim: str
    adres: str
    aciklama: str
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Depo) -> "DepoResponseDTO":
        return cls(
            id=entity.id,
            isim=entity.isim,
            adres=entity.adres,
            aciklama=entity.aciklama,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
