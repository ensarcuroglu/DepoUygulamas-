from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DailyStockExit(BaseModel):
    """Single daily stock-exit observation for one product."""

    tarih: date
    miktar: float = Field(..., ge=0)


class InputFeatures(BaseModel):
    """Demand forecast input features for a single product."""

    urun_id: int = Field(..., gt=0)
    tenant_id: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional SaaS tenant/customer context.",
    )
    stok_cikis_gecmisi: list[DailyStockExit] = Field(
        default_factory=list,
        max_length=730,
        description="Gunluk stok cikis serisi (en fazla 2 yil).",
    )
    mevcut_stok: float = Field(..., ge=0)
    min_stok: float = Field(..., ge=0)

    # Faz 2/3 icin opsiyonel exogenous sinyaller
    kategori_id: Optional[int] = Field(default=None, ge=1)
    marka_id: Optional[int] = Field(default=None, ge=1)
    tatil_gunleri: list[date] = Field(
        default_factory=list,
        description="Bilinen tatil/ozel gun tarih listesi (TR resmi tatiller dahil).",
    )
    kategori_ortalama_gunluk: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cold-start fallback icin kategori bazli gunluk medyan talep.",
    )
    marka_ortalama_gunluk: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cold-start fallback icin marka bazli gunluk medyan talep.",
    )

    @field_validator("stok_cikis_gecmisi")
    @classmethod
    def tarih_tekrari_olamaz(cls, value: list[DailyStockExit]) -> list[DailyStockExit]:
        tarihler = [item.tarih for item in value]
        if len(tarihler) != len(set(tarihler)):
            raise ValueError("stok_cikis_gecmisi icinde ayni tarih birden fazla kez bulunamaz.")
        return value

    @model_validator(mode="after")
    def tarihe_gore_sirala(self) -> "InputFeatures":
        self.stok_cikis_gecmisi = sorted(self.stok_cikis_gecmisi, key=lambda item: item.tarih)
        return self


class GunlukTahminNoktasi(BaseModel):
    """Tek bir gun icin nokta tahmini ve guven araligi."""

    tarih: date
    tahmin: float = Field(..., ge=0)
    alt_sinir: float = Field(..., ge=0)
    ust_sinir: float = Field(..., ge=0)


class TrendBilgisi(BaseModel):
    yon: Literal["pozitif", "negatif", "stabil"]
    degisim_orani: float
    etiket: str


class PredictionResult(BaseModel):
    """Demand forecast output for a single product."""

    urun_id: int = Field(..., gt=0)
    tahmin_gun: int = Field(default=30, gt=0)
    tahmini_talep: float = Field(..., ge=0)
    gunluk_ortalama_talep: float = Field(..., ge=0)
    onerilen_ikmal_miktari: float = Field(..., ge=0)
    guvenli_stok: float = Field(default=0.0, ge=0)
    stok_riski: Literal["yok", "dikkat", "kritik"]
    talep_sinyali: Literal["dusuk", "normal", "yuksek"]
    veri_guven_skoru: float = Field(..., ge=0, le=1)
    uyarilar: list[str] = Field(default_factory=list)

    # Cok-adimli tahmin + guven araligi (Recharts icin)
    gunluk_tahmin_serisi: list[GunlukTahminNoktasi] = Field(default_factory=list)
    trend: Optional[TrendBilgisi] = None
    model_versiyonu: str = Field(default="baseline-ma-1.0")
    son_hesaplanma: Optional[str] = Field(default=None, description="ISO-8601 zaman damgasi.")
