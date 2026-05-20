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


class ParquetVeriSetiDTO(BaseModel):
    """Backtest icin kullanilabilir parquet dosyasi."""

    dosya: str = Field(..., description="ml_models/talep_tahmin/data/raw altindaki dosya adi.")
    boyut_bytes: int = Field(..., ge=0)
    satir_sayisi: int = Field(..., ge=0)
    urun_sayisi: int = Field(..., ge=0)


class ParquetBacktestRequestDTO(BaseModel):
    """Parquet uzerinde backtest calistirma istegi."""

    dosya: str = Field(..., min_length=1, max_length=200)
    tahmin_gun: int = Field(default=7)
    urun_id: Optional[int] = Field(default=None, ge=1)


class ParquetBacktestUrunSonucDTO(BaseModel):
    """Tek bir urun icin backtest sonucu."""

    urun_id: int = Field(..., ge=1)
    gercek_talep: float = Field(..., ge=0)
    tahmini_talep: float = Field(..., ge=0)
    mae: float = Field(..., ge=0)
    mape: float = Field(..., ge=0, description="Yuzde cinsinden (0-100+).")
    veri_guven_skoru: float = Field(..., ge=0, le=1)
    stok_riski: Literal["yok", "dikkat", "kritik"]
    talep_sinyali: Literal["dusuk", "normal", "yuksek"]


class ParquetBacktestSonucDTO(BaseModel):
    """Parquet veri seti uzerinde calisan backtest ozeti + per-urun detaylari."""

    veri_kaynagi: str
    tahmin_gun: int
    urun_sayisi: int = Field(..., ge=0)
    mae: float = Field(..., ge=0, description="Per-urun MAE ortalamasi.")
    mape: float = Field(..., ge=0, description="Per-urun MAPE ortalamasi (yuzde).")
    model_versiyonu: str
    sonuclar: list[ParquetBacktestUrunSonucDTO] = Field(default_factory=list)
