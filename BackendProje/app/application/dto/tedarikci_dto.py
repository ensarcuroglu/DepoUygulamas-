"""
Tedarikçi veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.tedarikci import Tedarikci


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class TedarikciOlusturRequestDTO(BaseModel):
    firma_adi: str = Field(..., min_length=1, max_length=200, description="Firma adı")
    iletisim_kisi: Optional[str] = Field(None, max_length=200)
    telefon: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    adres: Optional[str] = Field(None, max_length=500)
    vergi_no: Optional[str] = Field(None, max_length=20)

    @field_validator("firma_adi")
    @classmethod
    def firma_adi_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Firma adı boş olamaz.")
        return v.strip()


class TedarikciGuncelleRequestDTO(BaseModel):
    firma_adi: Optional[str] = Field(None, min_length=1, max_length=200)
    iletisim_kisi: Optional[str] = Field(None, max_length=200)
    telefon: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    adres: Optional[str] = Field(None, max_length=500)
    vergi_no: Optional[str] = Field(None, max_length=20)
    aktif: Optional[bool] = None

    @field_validator("firma_adi")
    @classmethod
    def firma_adi_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Firma adı boş olamaz.")
        return v.strip() if v else v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class TedarikciResponseDTO(BaseModel):
    id: int
    firma_adi: str
    iletisim_kisi: Optional[str]
    telefon: Optional[str]
    email: Optional[str]
    adres: Optional[str]
    vergi_no: Optional[str]
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Tedarikci) -> "TedarikciResponseDTO":

        if entity.id is None:
            raise ValueError("TedarikciResponseDTO oluşturulamadı: entity.id boş olamaz.")
        
        return cls(
            id=entity.id,
            firma_adi=entity.firma_adi,
            iletisim_kisi=entity.iletisim_kisi,
            telefon=entity.telefon,
            email=entity.email,
            adres=entity.adres,
            vergi_no=entity.vergi_no,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )
