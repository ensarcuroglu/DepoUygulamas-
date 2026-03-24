"""
Rapor veri transfer nesneleri (DTO).

Sablon, Log, Schedule için request/response DTO'ları.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────
# RAPOR ŞABLONU DTO'LARI
# ─────────────────────────────────────────

class RaporSablonuOlusturRequestDTO(BaseModel):
    ad: str = Field(..., min_length=1, max_length=200)
    tur: str = Field(..., min_length=1)
    aciklama: Optional[str] = ""
    config: Optional[dict] = None

    @field_validator("ad")
    @classmethod
    def ad_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Şablon adı boş bırakılamaz.")
        return v.strip()


class RaporSablonuGuncelleRequestDTO(BaseModel):
    ad: Optional[str] = None
    tur: Optional[str] = None
    aciklama: Optional[str] = None
    config: Optional[dict] = None
    is_aktif: Optional[bool] = None


class RaporSablonuResponseDTO(BaseModel):
    id: int
    ad: str
    tur: str
    aciklama: str
    config: Optional[Any] = None
    is_aktif: bool
    olusturan_kullanici_id: Optional[int] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "RaporSablonuResponseDTO":
        return cls(
            id=entity.id,
            ad=entity.ad,
            tur=entity.tur,
            aciklama=entity.aciklama,
            config=entity.config,
            is_aktif=entity.is_aktif,
            olusturan_kullanici_id=entity.olusturan_kullanici_id,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
        )


# ─────────────────────────────────────────
# RAPOR LOGU DTO'LARI
# ─────────────────────────────────────────

class RaporLoguResponseDTO(BaseModel):
    id: int
    sablon_id: Optional[int] = None
    kullanici_id: int
    parametreler: Optional[Any] = None
    durum: str
    hata_mesaji: Optional[str] = None
    olusturma_tarihi: datetime
    tamamlanma_tarihi: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "RaporLoguResponseDTO":
        return cls(
            id=entity.id,
            sablon_id=entity.sablon_id,
            kullanici_id=entity.kullanici_id,
            parametreler=entity.parametreler,
            durum=entity.durum,
            hata_mesaji=entity.hata_mesaji,
            olusturma_tarihi=entity.olusturma_tarihi,
            tamamlanma_tarihi=entity.tamamlanma_tarihi,
        )


# ─────────────────────────────────────────
# RAPOR SCHEDULE DTO'LARI
# ─────────────────────────────────────────

class RaporScheduleOlusturRequestDTO(BaseModel):
    sablon_id: int = Field(..., gt=0)
    sablon_adi: str = Field(..., min_length=1)
    periyod: str = Field(..., pattern=r"^(gunluk|haftalik|aylik)$")
    saat: str = Field(..., pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    alici_emailler: Optional[List[str]] = None
    format: Optional[str] = Field("pdf", pattern=r"^(pdf|excel)$")


class RaporScheduleGuncelleRequestDTO(BaseModel):
    sablon_adi: Optional[str] = None
    periyod: Optional[str] = Field(None, pattern=r"^(gunluk|haftalik|aylik)$")
    saat: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    alici_emailler: Optional[List[str]] = None
    format: Optional[str] = Field(None, pattern=r"^(pdf|excel)$")
    is_aktif: Optional[bool] = None


class RaporScheduleResponseDTO(BaseModel):
    id: int
    sablon_id: int
    sablon_adi: str
    periyod: str
    saat: str
    alici_emailler: Optional[List[str]] = None
    format: str
    is_aktif: bool
    son_calistirilma: Optional[datetime] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "RaporScheduleResponseDTO":
        return cls(
            id=entity.id,
            sablon_id=entity.sablon_id,
            sablon_adi=entity.sablon_adi,
            periyod=entity.periyod,
            saat=entity.saat,
            alici_emailler=entity.alici_emailler,
            format=entity.format,
            is_aktif=entity.is_aktif,
            son_calistirilma=entity.son_calistirilma,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
        )
