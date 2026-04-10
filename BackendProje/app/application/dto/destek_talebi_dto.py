"""
Destek Talebi veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field

from app.core.entities.destek_talebi import DestekTalebi


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class DestekTalebiOlusturRequestDTO(BaseModel):
    konu: str = Field(..., min_length=1, max_length=200)
    kategori: Literal["Teknik", "Stok", "Sistem", "Diger"]
    oncelik: Literal["Normal", "Yüksek", "Düşük"] = "Normal"
    aciklama: str = Field(..., min_length=1, max_length=5000)


class DestekTalebiGuncelleRequestDTO(BaseModel):
    durum: Optional[Literal["Açık", "İşlemde", "Çözüldü"]] = None
    admin_cevabi: Optional[str] = Field(None, max_length=5000)
    oncelik: Optional[Literal["Normal", "Yüksek", "Düşük"]] = None


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class DestekTalebiResponseDTO(BaseModel):
    id: int
    kullanici_id: int
    konu: str
    kategori: str
    oncelik: str
    aciklama: str
    durum: str
    admin_cevabi: Optional[str] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: DestekTalebi) -> "DestekTalebiResponseDTO":

        if entity.id is None:
            raise ValueError("DestekTalebiResponseDTO oluşturulamadı: entity.id boş olamaz.")
        
        return cls(
            id=entity.id,
            kullanici_id=entity.kullanici_id,
            konu=entity.konu,
            kategori=entity.kategori,
            oncelik=entity.oncelik,
            aciklama=entity.aciklama,
            durum=entity.durum,
            admin_cevabi=entity.admin_cevabi,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
        )
