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
    kategori_id: Optional[int] = None
    marka_id: Optional[int] = None


class GunlukTalepDTO(BaseModel):
    tarih: date
    miktar: float = Field(..., ge=0)


class GunlukTahminDTO(BaseModel):
    tarih: date
    tahmin: float = Field(..., ge=0)
    alt_sinir: float = Field(default=0.0, ge=0)
    ust_sinir: float = Field(default=0.0, ge=0)


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
    model_versiyonu: str = "baseline-ma-1.1"
    son_hesaplanma: Optional[str] = None


class RiskliUrunDTO(BaseModel):
    """Toplu 'riskli urunler' listesi icin ozet kayit."""

    urun: TalepTahminUrunOzetDTO
    tahmin_gun: int
    tahmini_talep: float = Field(..., ge=0)
    gunluk_ortalama_talep: float = Field(..., ge=0)
    onerilen_ikmal_miktari: float = Field(..., ge=0)
    stok_riski: Literal["yok", "dikkat", "kritik"]
    talep_sinyali: Literal["dusuk", "normal", "yuksek"]
    veri_guven_skoru: float = Field(..., ge=0, le=1)
    son_hesaplanma: Optional[str] = None


class BacktestOzetDTO(BaseModel):
    """Modelin son N gun icindeki accuracy ozeti."""

    tahmin_gun: int
    mae: float = Field(..., ge=0)
    mape: float = Field(..., ge=0)
    urun_sayisi: int = Field(..., ge=0)
    model_versiyonu: str
