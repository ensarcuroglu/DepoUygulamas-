"""
Sistem Log veri transfer nesneleri (DTO).

SistemLog salt okunur modüldür — sadece listeleme DTO'su vardır.
Frontend'den log oluşturma için basit bir request DTO da dahildir.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field

from app.core.entities.sistem_log import SistemLog


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class SistemLogOlusturRequestDTO(BaseModel):
    islem_tipi: str = Field(..., max_length=50)
    modul: str = Field(..., max_length=200)
    detay: Optional[str] = Field(None, max_length=5000)
    eski_veri: Optional[dict] = None
    yeni_veri: Optional[dict] = None


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class SistemLogResponseDTO(BaseModel):
    id: int
    kullanici_id: Optional[int] = None
    islem_tipi: str
    modul: str
    detay: Optional[str] = None
    eski_veri: Optional[Any] = None
    yeni_veri: Optional[Any] = None
    tarih: datetime

    model_config = {"from_attributes": True}

    @staticmethod
    def _to_utc_aware(value: datetime) -> datetime:
        """
        VeritabanÄ±ndan timezone'suz (naive) gelen datetime deÄŸerlerini UTC kabul ederek
        timezone-aware hale getirir.
        """
        if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @classmethod
    def from_entity(cls, entity: SistemLog) -> "SistemLogResponseDTO":
        return cls(
            id=entity.id,
            kullanici_id=entity.kullanici_id,
            islem_tipi=entity.islem_tipi,
            modul=entity.modul,
            detay=entity.detay,
            eski_veri=entity.eski_veri,
            yeni_veri=entity.yeni_veri,
            tarih=cls._to_utc_aware(entity.tarih),
        )
