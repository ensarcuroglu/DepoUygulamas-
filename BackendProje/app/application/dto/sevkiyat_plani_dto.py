"""
Sevkiyat Planı veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.sevkiyat_plani import SevkiyatDurum

_IZINLI_DURUMLAR = {
    SevkiyatDurum.PLANLANDI,
    SevkiyatDurum.YUKLENIYOR,
    SevkiyatDurum.YOLDA,
    SevkiyatDurum.TESLIM_EDILDI,
}


def _dogrula_durum(v: str | None) -> str | None:
    if v is not None and v not in _IZINLI_DURUMLAR:
        raise ValueError(f"Geçersiz durum: '{v}'. İzin verilen: {_IZINLI_DURUMLAR}")
    return v


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class SevkiyatPlaniOlusturRequestDTO(BaseModel):
    """Yeni sevkiyat planı oluşturma isteği."""

    siparis_id: int = Field(..., gt=0)
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    sofor_telefon: Optional[str] = Field(None, max_length=20)
    depo_kapi: Optional[str] = Field(None, max_length=20)
    yukleme_tarihi: Optional[date] = None
    cikis_saati: Optional[str] = Field(None, max_length=10)
    varis_saati: Optional[str] = Field(None, max_length=10)
    durum: str = Field(default=SevkiyatDurum.PLANLANDI, max_length=20)
    notlar: str = Field(default="", max_length=2000)

    @field_validator("durum")
    @classmethod
    def gecerli_durum(cls, v: str) -> str:
        if v != SevkiyatDurum.PLANLANDI:
            raise ValueError(
                f"Sevkiyat planı yalnızca '{SevkiyatDurum.PLANLANDI}' durumunda oluşturulabilir."
            )
        return v


class SevkiyatPlaniGuncelleRequestDTO(BaseModel):
    """Mevcut sevkiyat planı güncelleme isteği — tüm alanlar opsiyoneldir."""

    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    sofor_telefon: Optional[str] = Field(None, max_length=20)
    depo_kapi: Optional[str] = Field(None, max_length=20)
    yukleme_tarihi: Optional[date] = None
    cikis_saati: Optional[str] = Field(None, max_length=10)
    varis_saati: Optional[str] = Field(None, max_length=10)
    durum: Optional[str] = Field(None, max_length=20)
    notlar: Optional[str] = Field(None, max_length=2000)

    @field_validator("durum")
    @classmethod
    def gecerli_durum(cls, v: Optional[str]) -> Optional[str]:
        return _dogrula_durum(v)


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class SevkiyatKalemiResponseDTO(BaseModel):
    """Sevkiyat kalemi response — hangi sipariş kaleminden ne kadar yüklendi."""

    id: int
    sevkiyat_id: int
    siparis_kalemi_id: int
    urun_id: int
    miktar: int

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "SevkiyatKalemiResponseDTO":
        return cls(
            id=entity.id,
            sevkiyat_id=entity.sevkiyat_id,
            siparis_kalemi_id=entity.siparis_kalemi_id,
            urun_id=entity.urun_id,
            miktar=entity.miktar,
        )


class SevkiyatPlaniResponseDTO(BaseModel):
    """Sevkiyat planı response DTO."""

    id: int
    siparis_id: int
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    sofor_telefon: Optional[str] = None
    depo_kapi: Optional[str] = None
    yukleme_tarihi: Optional[date] = None
    cikis_saati: Optional[str] = None
    varis_saati: Optional[str] = None
    durum: str
    notlar: str
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    kalemler: List[SevkiyatKalemiResponseDTO] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "SevkiyatPlaniResponseDTO":
        kalemler = [
            SevkiyatKalemiResponseDTO.from_entity(k)
            for k in getattr(entity, "kalemler", [])
        ]
        return cls(
            id=entity.id,
            siparis_id=entity.siparis_id,
            tir_plaka=entity.tir_plaka,
            sofor_adi=entity.sofor_adi,
            sofor_telefon=entity.sofor_telefon,
            depo_kapi=entity.depo_kapi,
            yukleme_tarihi=entity.yukleme_tarihi,
            cikis_saati=entity.cikis_saati,
            varis_saati=entity.varis_saati,
            durum=entity.durum,
            notlar=entity.notlar,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
            kalemler=kalemler,
        )
