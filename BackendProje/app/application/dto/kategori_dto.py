"""
Kategori veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.kategori import Kategori


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class KategoriOlusturRequestDTO(BaseModel):
    isim: str = Field(..., min_length=1, max_length=200, description="Kategori adı")
    aciklama: str = Field(default="", max_length=2000)
    ikon: Optional[str] = Field(default="FolderOpen", max_length=50)

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Kategori ismi boş olamaz.")
        return v.strip()


class KategoriGuncelleRequestDTO(BaseModel):
    isim: Optional[str] = Field(None, min_length=1, max_length=200)
    aciklama: Optional[str] = Field(None, max_length=2000)
    ikon: Optional[str] = Field(None, max_length=50)
    aktif: Optional[bool] = None

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Kategori ismi boş olamaz.")
        return v.strip() if v else v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class KategoriResponseDTO(BaseModel):
    id: int
    isim: str
    aciklama: str
    ikon: str
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Kategori) -> "KategoriResponseDTO":
        return cls(
            id=entity.id,
            isim=entity.isim,
            aciklama=entity.aciklama,
            ikon=entity.ikon,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
