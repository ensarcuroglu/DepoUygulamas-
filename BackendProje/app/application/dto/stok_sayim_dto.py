"""
Stok Sayım veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class StokSayimOlusturRequestDTO(BaseModel):
    """Yeni stok sayımı oluşturma isteği."""

    aciklama: str = Field(default="", max_length=500)


class StokSayimKalemiKaydetRequestDTO(BaseModel):
    """Sayım kalemi kaydetme (upsert) isteği."""

    urun_id: int = Field(..., gt=0)
    sayilan_miktar: int = Field(..., ge=0)
    notlar: str = Field(default="", max_length=500)


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class StokSayimKalemiResponseDTO(BaseModel):
    """Sayım kalemi response DTO."""

    id: int
    sayim_id: int
    urun_id: int
    sayilan_miktar: int
    notlar: str
    user_id: Optional[int] = None
    sayim_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "StokSayimKalemiResponseDTO":
        return cls(
            id=entity.id,
            sayim_id=entity.sayim_id,
            urun_id=entity.urun_id,
            sayilan_miktar=entity.sayilan_miktar,
            notlar=entity.notlar,
            user_id=entity.user_id,
            sayim_tarihi=entity.sayim_tarihi,
        )


class StokSayimResponseDTO(BaseModel):
    """Stok sayım response DTO."""

    id: int
    sayim_no: str
    aciklama: str
    baslangic_tarihi: datetime
    bitis_tarihi: Optional[datetime] = None
    durum: str
    kontrol_eden_user_id: Optional[int] = None
    onaylayan_user_id: Optional[int] = None
    olusturma_tarihi: datetime
    sayim_kalemleri: List[StokSayimKalemiResponseDTO] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "StokSayimResponseDTO":
        return cls(
            id=entity.id,
            sayim_no=entity.sayim_no,
            aciklama=entity.aciklama,
            baslangic_tarihi=entity.baslangic_tarihi,
            bitis_tarihi=entity.bitis_tarihi,
            durum=entity.durum,
            kontrol_eden_user_id=entity.kontrol_eden_user_id,
            onaylayan_user_id=entity.onaylayan_user_id,
            olusturma_tarihi=entity.olusturma_tarihi,
            sayim_kalemleri=[
                StokSayimKalemiResponseDTO.from_entity(k)
                for k in entity.sayim_kalemleri
            ],
        )


# ─────────────────────────────────────────
# VARYANS DTO'LARI
# ─────────────────────────────────────────

class VaryansKalemDTO(BaseModel):
    urun_id: int
    urun_adi: str
    beklenen: int
    sayilan: int
    fark: int
    yuzde: float
    notlar: str = ""


class VaryansResponseDTO(BaseModel):
    sayim_no: str
    referans_tarih: Optional[datetime] = None
    varyanslar: List[VaryansKalemDTO] = []
    toplam_sapma: int = 0
    sayilan_urun_sayisi: int = 0
    sapma_orani: float = 0.0
