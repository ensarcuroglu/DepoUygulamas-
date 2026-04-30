from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field


class TalepTahminUrunOzetDTO(BaseModel):
    id: int
    isim: str
    barkod: Optional[str] = None
    min_stok: int
    stok_miktari: int


class GunlukTalepDTO(BaseModel):
    tarih: date
    miktar: float = Field(..., ge=0)


class GunlukTahminDTO(BaseModel):
    tarih: date
    tahmin: float = Field(..., ge=0)


class TalepTrendDTO(BaseModel):
    yon: Literal["pozitif", "negatif", "stabil"]
    degisim_orani: float
    etiket: str


class TalepTahminResponseDTO(BaseModel):
    urun: TalepTahminUrunOzetDTO
    tahmin_gun: int
    gecmis_gunluk_seri: list[GunlukTalepDTO]
    gelecek_gunluk_tahmin: list[GunlukTahminDTO]
    tahmini_talep: float = Field(..., ge=0)
    gunluk_ortalama_talep: float = Field(..., ge=0)
    guvenli_stok: float = Field(..., ge=0)
    onerilen_ikmal_miktari: float = Field(..., ge=0)
    stok_riski: Literal["yok", "dikkat", "kritik"]
    talep_sinyali: Literal["dusuk", "normal", "yuksek"]
    veri_guven_skoru: float = Field(..., ge=0, le=1)
    trend: TalepTrendDTO
    uyarilar: list[str] = Field(default_factory=list)

