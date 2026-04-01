"""
Ürün veri transfer nesneleri (DTO).

Request DTO'ları: Frontend'den gelen veriyi alır ve doğrular.
Response DTO'ları: Domain entity'sinden oluşturulur; frontend'e döner.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class UrunOlusturRequestDTO(BaseModel):
    """Yeni ürün oluşturma isteği."""

    isim: str = Field(..., min_length=1, max_length=200, description="Ürün adı")
    marka_id: Optional[int] = Field(None, gt=0)
    kategori_id: Optional[int] = Field(None, gt=0)
    tedarikci_id: Optional[int] = Field(None, gt=0)
    ean: Optional[str] = Field(None, pattern=r"^\d{8,14}$", description="EAN-8, EAN-13 veya EAN-14 (numerik)")
    barkod: Optional[str] = Field(None, max_length=100, description="Barkod / ürün kodu (alfanümerik)")
    ic_adet: int = Field(default=1, ge=1, description="Koli başına iç adet")
    gramaj: Optional[float] = Field(None, ge=0, description="Birim gramaj (kg)")
    birim: str = Field(default="Adet", max_length=20)
    fiyat: float = Field(default=0.0, ge=0, description="Birim fiyat")
    min_stok: int = Field(default=10, ge=0, description="Kritik stok eşiği")
    aciklama: str = Field(default="", max_length=2000)

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Ürün ismi boşluk bırakılamaz.")
        return v.strip()

    @field_validator("birim")
    @classmethod
    def gecerli_birim(cls, v: str) -> str:
        izinli = {"Adet", "Kg", "Metre", "Kutu", "Litre", "Paket"}
        if v not in izinli:
            raise ValueError(f"Geçersiz birim: '{v}'. İzin verilen: {izinli}")
        return v


class UrunGuncelleRequestDTO(BaseModel):
    """Mevcut ürün güncelleme isteği — tüm alanlar opsiyoneldir."""

    isim: Optional[str] = Field(None, min_length=1, max_length=200)
    marka_id: Optional[int] = Field(None, gt=0)
    kategori_id: Optional[int] = Field(None, gt=0)
    tedarikci_id: Optional[int] = Field(None, gt=0)
    ean: Optional[str] = Field(None, pattern=r"^\d{8,14}$")
    barkod: Optional[str] = Field(None, max_length=100)
    ic_adet: Optional[int] = Field(None, ge=1)
    gramaj: Optional[float] = Field(None, ge=0)
    birim: Optional[str] = Field(None, max_length=20)
    fiyat: Optional[float] = Field(None, ge=0)
    min_stok: Optional[int] = Field(None, ge=0)
    aciklama: Optional[str] = Field(None, max_length=2000)
    aktif: Optional[bool] = None

    @field_validator("isim")
    @classmethod
    def isim_bos_olamaz(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Ürün ismi boşluk bırakılamaz.")
        return v.strip() if v else v

    @field_validator("birim")
    @classmethod
    def gecerli_birim(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            izinli = {"Adet", "Kg", "Metre", "Kutu", "Litre", "Paket"}
            if v not in izinli:
                raise ValueError(f"Geçersiz birim: '{v}'. İzin verilen: {izinli}")
        return v


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class MarkaOzetDTO(BaseModel):
    id: int
    isim: str

    model_config = {"from_attributes": True}


class KategoriOzetDTO(BaseModel):
    id: int
    isim: str

    model_config = {"from_attributes": True}


class UrunListResponseDTO(BaseModel):
    """Ürün listesi için hafif response — N+1 önlemek için tedarikçisiz."""

    id: int
    isim: str
    barkod: Optional[str]
    ean: Optional[str]
    aciklama: str
    ic_adet: int
    gramaj: Optional[float]
    birim: str
    fiyat: float
    min_stok: int
    stok_miktari: int
    durum: str
    aktif: bool
    marka_id: Optional[int]
    kategori_id: Optional[int]

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "UrunListResponseDTO":
        return cls(
            id=entity.id,
            isim=entity.isim,
            barkod=entity.barkod,
            ean=entity.ean,
            aciklama=entity.aciklama,
            ic_adet=entity.ic_adet,
            gramaj=entity.gramaj,
            birim=entity.birim,
            fiyat=entity.fiyat,
            min_stok=entity.min_stok,
            stok_miktari=entity.stok_miktari,
            durum=entity.durum,
            aktif=entity.aktif,
            marka_id=entity.marka_id,
            kategori_id=entity.kategori_id,
        )


class UrunResponseDTO(BaseModel):
    """Tek ürün detay response — marka ve kategori dahil."""

    id: int
    isim: str
    barkod: Optional[str]
    ean: Optional[str]
    ic_adet: int
    gramaj: Optional[float]
    birim: str
    fiyat: float
    min_stok: int
    aciklama: str
    stok_miktari: int
    durum: str
    aktif: bool
    marka_id: Optional[int]
    kategori_id: Optional[int]
    tedarikci_id: Optional[int]
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "UrunResponseDTO":
        return cls(
            id=entity.id,
            isim=entity.isim,
            barkod=entity.barkod,
            ean=entity.ean,
            ic_adet=entity.ic_adet,
            gramaj=entity.gramaj,
            birim=entity.birim,
            fiyat=entity.fiyat,
            min_stok=entity.min_stok,
            aciklama=entity.aciklama,
            stok_miktari=entity.stok_miktari,
            durum=entity.durum,
            aktif=entity.aktif,
            marka_id=entity.marka_id,
            kategori_id=entity.kategori_id,
            tedarikci_id=entity.tedarikci_id,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
        )
