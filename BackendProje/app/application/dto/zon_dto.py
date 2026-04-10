"""
Zon veri transfer nesneleri (DTO).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.core.entities.zon import Zon, ZonTipi


class ZonOlusturRequestDTO(BaseModel):
    depo_id: int = Field(..., gt=0, description="Bagli oldugu depo ID")
    isim: str = Field(..., min_length=1, max_length=100)
    tip: str = Field(..., min_length=1, max_length=30, description="Zon tipi")
    kod: str = Field(..., min_length=1, max_length=10, description="Zon kodu")
    aciklama: str = Field(default="", max_length=2000)
    sira: int = Field(default=0, ge=0)

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Zon ismi bos olamaz.")
        return v.strip()

    @field_validator("kod")
    @classmethod
    def kod_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Zon kodu bos olamaz.")
        return v.strip().upper()

    @field_validator("tip")
    @classmethod
    def tip_gecerli_olmali(cls, v: str) -> str:
        tip = v.strip()
        if not ZonTipi.gecerli_mi(tip):
            gecerli = ", ".join(sorted(ZonTipi.tipler()))
            raise ValueError(f"Gecersiz zon tipi: {tip}. Gecerli degerler: {gecerli}")
        return tip


class ZonGuncelleRequestDTO(BaseModel):
    depo_id: Optional[int] = Field(None, gt=0)
    isim: Optional[str] = Field(None, min_length=1, max_length=100)
    tip: Optional[str] = Field(None, min_length=1, max_length=30)
    kod: Optional[str] = Field(None, min_length=1, max_length=10)
    aciklama: Optional[str] = Field(None, max_length=2000)
    sira: Optional[int] = Field(None, ge=0)
    aktif: Optional[bool] = None

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Zon ismi bos olamaz.")
        return v.strip() if v else v

    @field_validator("kod")
    @classmethod
    def kod_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Zon kodu bos olamaz.")
        return v.strip().upper() if v else v

    @field_validator("tip")
    @classmethod
    def tip_gecerli_olmali(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        tip = v.strip()
        if not ZonTipi.gecerli_mi(tip):
            gecerli = ", ".join(sorted(ZonTipi.tipler()))
            raise ValueError(f"Gecersiz zon tipi: {tip}. Gecerli degerler: {gecerli}")
        return tip


class ZonResponseDTO(BaseModel):
    id: int
    depo_id: int
    isim: str
    tip: str
    kod: str
    aciklama: str
    sira: int
    aktif: bool
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Zon) -> "ZonResponseDTO":

        if entity.id is None:
            raise ValueError("ZonResponseDTO oluşturulamadı: entity.id boş olamaz.")

        return cls(
            id=entity.id,
            depo_id=entity.depo_id,
            isim=entity.isim,
            tip=entity.tip,
            kod=entity.kod,
            aciklama=entity.aciklama,
            sira=entity.sira,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
        )

