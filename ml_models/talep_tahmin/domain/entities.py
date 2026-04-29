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
        max_length=90,
        description="Last 90 days of product-level stock exits as a time series.",
    )
    mevcut_stok: float = Field(..., ge=0)
    min_stok: float = Field(..., ge=0)

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


class PredictionResult(BaseModel):
    """Demand forecast output for a single product."""

    urun_id: int = Field(..., gt=0)
    tahmin_gun: int = Field(default=30, gt=0)
    tahmini_talep: float = Field(..., ge=0)
    gunluk_ortalama_talep: float = Field(..., ge=0)
    onerilen_ikmal_miktari: float = Field(..., ge=0)
    stok_riski: Literal["yok", "dikkat", "kritik"]
    talep_sinyali: Literal["dusuk", "normal", "yuksek"]
    veri_guven_skoru: float = Field(..., ge=0, le=1)
    uyarilar: list[str] = Field(default_factory=list)
