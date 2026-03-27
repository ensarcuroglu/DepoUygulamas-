"""
Stok Hareketi veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class StokHareketiOlusturRequestDTO(BaseModel):
    """Yeni stok hareketi oluşturma isteği."""

    urun_id: int = Field(..., gt=0, description="Harekete konu olan ürün ID")
    hareket_tipi: Literal["giris", "cikis"] = Field(
        ..., description="'giris' veya 'cikis'"
    )
    miktar: int = Field(..., gt=0, description="Hareket miktarı (koli)")

    # Opsiyonel bağlamsal alanlar
    lot_id: Optional[int] = Field(None, gt=0, description="İlişkilendirilecek LOT ID")
    palet_id: Optional[int] = Field(None, gt=0, description="İlişkilendirilecek palet ID")
    raf_id: Optional[int] = Field(None, gt=0, description="Giriş için hedef raf ID")
    siparis_no: Optional[str] = Field(
        None, max_length=100, description="Çıkış için sipariş numarası"
    )
    tir_plaka: Optional[str] = Field(
        None, max_length=50, description="Çıkış için TIR plakası"
    )
    depo_kapi: Optional[str] = Field(
        None, max_length=50, description="Çıkış için depo kapısı"
    )
    barkodlar: Optional[List[str]] = Field(
        None, description="Taranan barkodlar listesi"
    )
    aciklama: str = Field(default="", max_length=1000)

    @field_validator("barkodlar")
    @classmethod
    def barkodlar_validasyonu(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Barkod listesindeki her elemanın uzunluğunu kontrol eder."""
        if v is not None:
            for barkod in v:
                if len(barkod) > 50:
                    raise ValueError(f"Barkod çok uzun ({len(barkod)} > 50 karakter): {barkod}")
        return v

    @model_validator(mode="after")
    def cikis_validasyonu(self) -> "StokHareketiOlusturRequestDTO":
        """Çıkış hareketinde sipariş no veya açıklama zorunluluğu kontrolü."""
        if self.hareket_tipi == "cikis":
            if not self.siparis_no and not self.aciklama:
                raise ValueError(
                    "Çıkış hareketi için 'siparis_no' veya 'aciklama' alanlarından en az biri zorunludur."
                )
        return self


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class KullaniciOzetDTO(BaseModel):
    id: int
    kullanici_adi: str
    ad_soyad: str

    model_config = {"from_attributes": True}


class StokHareketiResponseDTO(BaseModel):
    """Stok hareketi response — oluşturma ve listeleme için."""

    id: int
    urun_id: int
    lot_id: Optional[int]
    palet_id: Optional[int]
    raf_id: Optional[int]
    hareket_tipi: str
    miktar: int
    siparis_no: Optional[str]
    tir_plaka: Optional[str]
    depo_kapi: Optional[str]
    barkodlar: Optional[List[str]]
    aciklama: str
    kullanici_id: Optional[int]
    tarih: datetime
    palet_no: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "StokHareketiResponseDTO":
        return cls(
            id=entity.id,
            urun_id=entity.urun_id,
            lot_id=entity.lot_id,
            palet_id=entity.palet_id,
            raf_id=entity.raf_id,
            hareket_tipi=entity.hareket_tipi,
            miktar=entity.miktar,
            siparis_no=entity.siparis_no,
            tir_plaka=entity.tir_plaka,
            depo_kapi=entity.depo_kapi,
            barkodlar=entity.barkodlar,
            aciklama=entity.aciklama,
            kullanici_id=entity.kullanici_id,
            tarih=entity.tarih,
            palet_no=getattr(entity, "palet_no", None),
        )
