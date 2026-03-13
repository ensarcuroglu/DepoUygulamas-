"""
Sipariş veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class SiparisKalemiOlusturRequestDTO(BaseModel):
    """Tek sipariş kalemi."""

    urun_id: int = Field(..., gt=0)
    miktar: int = Field(..., gt=0, description="Sipariş edilen koli adedi")
    birim_fiyat: float = Field(..., ge=0, description="KDV hariç birim fiyat")
    kdv_orani: float = Field(default=18.0, ge=0, le=100, description="KDV oranı (%)")

    @property
    def toplam_kdv_dahil(self) -> float:
        return round(self.miktar * self.birim_fiyat * (1 + self.kdv_orani / 100), 2)


class SiparisOlusturRequestDTO(BaseModel):
    """Yeni sipariş oluşturma isteği."""

    musteri_adi: str = Field(..., min_length=1, max_length=200)
    teslimat_adresi: str = Field(..., min_length=1, max_length=500)
    teslimat_tarihi: date = Field(..., description="Planlanan teslimat tarihi")
    notlar: str = Field(default="", max_length=2000)
    kalemler: List[SiparisKalemiOlusturRequestDTO] = Field(
        ..., min_length=1, description="En az 1 kalem zorunludur"
    )

    @field_validator("musteri_adi")
    @classmethod
    def musteri_adi_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Müşteri adı boşluk bırakılamaz.")
        return v.strip()

    @field_validator("teslimat_tarihi")
    @classmethod
    def teslimat_tarihi_gecmiste_olamaz(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Teslimat tarihi geçmişte olamaz.")
        return v

    @model_validator(mode="after")
    def kalemler_farkli_urun(self) -> "SiparisOlusturRequestDTO":
        """Aynı ürün birden fazla kalemde tekrarlanmamalı."""
        urun_ids = [k.urun_id for k in self.kalemler]
        if len(urun_ids) != len(set(urun_ids)):
            raise ValueError(
                "Aynı ürün birden fazla kalemde yer alamaz. "
                "Miktarları tek kalemde birleştirin."
            )
        return self


class SiparisGuncelleRequestDTO(BaseModel):
    """Mevcut sipariş güncelleme isteği — tüm alanlar opsiyoneldir."""

    musteri_adi: Optional[str] = Field(None, min_length=1, max_length=200)
    teslimat_adresi: Optional[str] = Field(None, min_length=1, max_length=500)
    teslimat_tarihi: Optional[date] = None
    durum: Optional[str] = Field(
        None,
        description="Bekleme | Hazirlaniyor | YolaCikti | TeslimEdildi | Iptal",
    )
    notlar: Optional[str] = Field(None, max_length=2000)
    aktif: Optional[bool] = None

    @field_validator("durum")
    @classmethod
    def gecerli_durum(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        izinli = {"Bekleme", "Hazirlaniyor", "YolaCikti", "TeslimEdildi", "Iptal"}
        if v not in izinli:
            raise ValueError(f"Geçersiz durum: '{v}'. İzin verilen: {izinli}")
        return v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class SiparisKalemiResponseDTO(BaseModel):
    """Tek sipariş kalemi response."""

    id: int
    siparis_id: int
    urun_id: int
    miktar: int
    birim_fiyat: float
    kdv_orani: float
    toplam: float

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "SiparisKalemiResponseDTO":
        return cls(
            id=entity.id,
            siparis_id=entity.siparis_id,
            urun_id=entity.urun_id,
            miktar=entity.miktar,
            birim_fiyat=entity.birim_fiyat,
            kdv_orani=entity.kdv_orani,
            toplam=entity.toplam,
        )


class SiparisResponseDTO(BaseModel):
    """Sipariş liste görünümü — kalemsiz."""

    id: int
    siparis_no: str
    musteri_adi: str
    teslimat_adresi: str
    teslimat_tarihi: date
    durum: str
    top_miktar: int
    top_tutar: float
    notlar: str
    olusturan_kullanici_id: Optional[int]
    aktif: bool
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "SiparisResponseDTO":
        return cls(
            id=entity.id,
            siparis_no=entity.siparis_no,
            musteri_adi=entity.musteri_adi,
            teslimat_adresi=entity.teslimat_adresi,
            teslimat_tarihi=entity.teslimat_tarihi,
            durum=entity.durum,
            top_miktar=entity.top_miktar,
            top_tutar=entity.top_tutar,
            notlar=entity.notlar,
            olusturan_kullanici_id=entity.olusturan_kullanici_id,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
        )


class SiparisDetayResponseDTO(SiparisResponseDTO):
    """Sipariş detay görünümü — kalemler dahil."""

    kalemler: List[SiparisKalemiResponseDTO] = []

    @classmethod
    def from_entity(cls, entity) -> "SiparisDetayResponseDTO":
        base = SiparisResponseDTO.from_entity(entity)
        kalemler = [SiparisKalemiResponseDTO.from_entity(k) for k in entity.kalemler]
        return cls(**base.model_dump(), kalemler=kalemler)
