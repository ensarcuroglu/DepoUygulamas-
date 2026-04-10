"""
İrsaliye veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.core.entities.irsaliye import IrsaliyeDurum, BelgeTuru

_IZINLI_BELGE_TURLERI = {BelgeTuru.SEVK_IRSALIYESI, BelgeTuru.IADE_IRSALIYESI}
_IZINLI_DURUMLAR = {IrsaliyeDurum.TASLAK, IrsaliyeDurum.KESILDI, IrsaliyeDurum.GONDERILDI}


def _dogrula_belge_turu(v: str | None) -> str | None:
    if v is not None and v not in _IZINLI_BELGE_TURLERI:
        raise ValueError(f"Geçersiz belge türü: '{v}'. İzin verilen: {_IZINLI_BELGE_TURLERI}")
    return v


def _dogrula_durum(v: str | None) -> str | None:
    if v is not None and v not in _IZINLI_DURUMLAR:
        raise ValueError(f"Geçersiz durum: '{v}'. İzin verilen: {_IZINLI_DURUMLAR}")
    return v


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class IrsaliyeOlusturRequestDTO(BaseModel):
    """Yeni irsaliye oluşturma isteği."""

    siparis_id: int = Field(..., gt=0)
    sevkiyat_id: Optional[int] = Field(None, gt=0)
    irsaliye_tarihi: Optional[date] = None
    belge_turu: str = Field(default=BelgeTuru.SEVK_IRSALIYESI, max_length=50)
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)

    @field_validator("belge_turu")
    @classmethod
    def gecerli_belge_turu(cls, v: str) -> str:
        sonuc = _dogrula_belge_turu(v)
        if sonuc is None:
            raise ValueError("Belge türü boş olamaz.")
        return sonuc


class IrsaliyeGuncelleRequestDTO(BaseModel):
    """Mevcut irsaliye güncelleme isteği — tüm alanlar opsiyoneldir."""

    belge_turu: Optional[str] = Field(None, max_length=50)
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    durum: Optional[str] = Field(None, max_length=20)

    @field_validator("belge_turu")
    @classmethod
    def gecerli_belge_turu(cls, v: Optional[str]) -> Optional[str]:
        return _dogrula_belge_turu(v)

    @field_validator("durum")
    @classmethod
    def gecerli_durum(cls, v: Optional[str]) -> Optional[str]:
        return _dogrula_durum(v)


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class IrsaliyeResponseDTO(BaseModel):
    """İrsaliye response DTO."""

    id: int
    siparis_id: int
    sevkiyat_id: Optional[int] = None
    irsaliye_no: str
    irsaliye_tarihi: Optional[date] = None
    belge_turu: str
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: str
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "IrsaliyeResponseDTO":
        return cls(
            id=entity.id,
            siparis_id=entity.siparis_id,
            sevkiyat_id=entity.sevkiyat_id,
            irsaliye_no=entity.irsaliye_no,
            irsaliye_tarihi=entity.irsaliye_tarihi,
            belge_turu=entity.belge_turu,
            tir_plaka=entity.tir_plaka,
            sofor_adi=entity.sofor_adi,
            durum=entity.durum,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
        )


class IrsaliyeYazdirKalemDTO(BaseModel):
    """Yazdırma verisindeki tek kalem."""

    urun_id: int
    urun_isim: str
    miktar: int
    birim_fiyat: float
    kdv_orani: float
    toplam: float


class IrsaliyeYazdirSiparisDTO(BaseModel):
    """Yazdırma verisindeki sipariş özeti."""

    siparis_no: str
    musteri_adi: str
    teslimat_adresi: str
    teslimat_tarihi: str
    top_tutar: float
    top_miktar: int


class IrsaliyeYazdirIrsaliyeDTO(BaseModel):
    """Yazdırma verisindeki irsaliye bilgileri."""

    id: int
    irsaliye_no: str
    irsaliye_tarihi: str
    belge_turu: str
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: str


class IrsaliyeYazdirResponseDTO(BaseModel):
    """İrsaliye yazdırma verisi — irsaliye + sipariş + kalemler."""

    irsaliye: IrsaliyeYazdirIrsaliyeDTO
    siparis: IrsaliyeYazdirSiparisDTO
    kalemler: List[IrsaliyeYazdirKalemDTO]
