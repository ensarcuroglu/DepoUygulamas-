"""
Raf veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.raf import Raf


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class RafOlusturRequestDTO(BaseModel):
    depo_id: int = Field(..., gt=0, description="Bağlı olduğu depo ID")
    kod: str = Field(..., min_length=1, max_length=50, description="Raf kodu (ör: A-01)")
    bolge: str = Field(default="", max_length=100, description="Bölge adı")
    kapasite: int = Field(default=100, ge=1, description="Palet kapasitesi")

    @field_validator("kod")
    @classmethod
    def kod_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Raf kodu boş olamaz.")
        return v.strip()


class RafGuncelleRequestDTO(BaseModel):
    depo_id: Optional[int] = Field(None, gt=0)
    kod: Optional[str] = Field(None, min_length=1, max_length=50)
    bolge: Optional[str] = Field(None, max_length=100)
    kapasite: Optional[int] = Field(None, ge=1)
    aktif: Optional[bool] = None

    @field_validator("kod")
    @classmethod
    def kod_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Raf kodu boş olamaz.")
        return v.strip() if v else v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class RafResponseDTO(BaseModel):
    id: int
    depo_id: Optional[int]
    kod: str
    bolge: str
    kapasite: int
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Raf) -> "RafResponseDTO":
        return cls(
            id=entity.id,
            depo_id=entity.depo_id,
            kod=entity.kod,
            bolge=entity.bolge,
            kapasite=entity.kapasite,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
