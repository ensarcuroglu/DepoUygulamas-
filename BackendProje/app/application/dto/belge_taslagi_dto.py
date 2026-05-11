"""Belge taslagi DTO'lari."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class BelgeTaslagiOlusturRequestDTO(BaseModel):
    kaynak_dosya_yolu: Optional[str] = Field(None, max_length=500)
    belge_tipi: str = Field("IRSALIYE", max_length=50)
    ham_json: dict[str, Any]
    confidence_skoru: Optional[float] = Field(None, ge=0.0, le=1.0)
    olusturan_kullanici_id: Optional[int] = Field(None, gt=0)
    depo_id: int = Field(..., gt=0)


class BelgeTaslagiKalemOnayDTO(BaseModel):
    urun_id: Optional[int] = Field(None, gt=0)
    urun_kodu: Optional[str] = Field(None, max_length=100)
    ad: Optional[str] = Field(None, max_length=200)
    miktar: Optional[float] = Field(None, gt=0)
    birim: Optional[str] = Field(None, max_length=20)
    palet_no: Optional[str] = Field(None, max_length=30)
    lot_no: Optional[str] = Field(None, max_length=50)
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None


class BelgeTaslagiOnaylaRequestDTO(BaseModel):
    tedarikci_id: Optional[int] = Field(None, gt=0)
    tedarikci_adi: Optional[str] = Field(None, max_length=200)
    depo_id: Optional[int] = Field(None, gt=0)
    tarih: Optional[date] = None
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    kalemler: Optional[list[BelgeTaslagiKalemOnayDTO]] = None


class BelgeTaslagiReddetRequestDTO(BaseModel):
    neden: Optional[str] = Field(None, max_length=500)


class BelgeTaslagiResponseDTO(BaseModel):
    id: int
    kaynak_dosya_yolu: Optional[str] = None
    belge_tipi: str
    ham_json: dict[str, Any]
    durum: str
    confidence_skoru: float
    olusturan_kullanici_id: Optional[int] = None
    depo_id: int
    mal_kabul_irsaliye_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "BelgeTaslagiResponseDTO":
        return cls(
            id=entity.id,
            kaynak_dosya_yolu=entity.kaynak_dosya_yolu,
            belge_tipi=entity.belge_tipi,
            ham_json=entity.ham_json,
            durum=entity.durum,
            confidence_skoru=entity.confidence_skoru,
            olusturan_kullanici_id=entity.olusturan_kullanici_id,
            depo_id=entity.depo_id,
            mal_kabul_irsaliye_id=entity.mal_kabul_irsaliye_id,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
