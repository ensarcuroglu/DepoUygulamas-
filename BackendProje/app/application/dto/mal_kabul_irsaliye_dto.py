"""
Mal Kabul İrsaliyesi veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

from app.core.entities.mal_kabul_irsaliye import MalKabulDurum, KalemDurum

_IZINLI_DURUMLAR = {MalKabulDurum.ONAYLANDI, MalKabulDurum.TAMAMLANDI}


# ─────────────────────────────────────────
# KALEM DTO'LARI
# ─────────────────────────────────────────

class MalKabulKalemiOlusturDTO(BaseModel):
    """Yeni kalem oluşturma isteği (irsaliye oluşturma/güncelleme içinde)."""

    palet_no: str = Field(..., min_length=1, max_length=30)
    urun_id: int = Field(..., gt=0)
    lot_no: Optional[str] = Field(None, max_length=50)
    miktar: int = Field(..., gt=0)
    raf_id: Optional[int] = Field(None, gt=0)
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None


class MalKabulKalemiResponseDTO(BaseModel):
    """Kalem response."""

    id: int
    mal_kabul_irsaliyesi_id: int
    palet_no: str
    urun_id: int
    lot_no: Optional[str] = None
    miktar: int
    raf_id: Optional[int] = None
    durum: str
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    olusturma_tarihi: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "MalKabulKalemiResponseDTO":
        return cls(
            id=entity.id,
            mal_kabul_irsaliyesi_id=entity.mal_kabul_irsaliyesi_id,
            palet_no=entity.palet_no,
            urun_id=entity.urun_id,
            lot_no=entity.lot_no,
            miktar=entity.miktar,
            raf_id=entity.raf_id,
            durum=entity.durum,
            uretim_tarihi=entity.uretim_tarihi,
            son_kullanma_tarihi=entity.son_kullanma_tarihi,
            olusturma_tarihi=entity.olusturma_tarihi,
        )


# ─────────────────────────────────────────
# İRSALİYE REQUEST DTO'LARI
# ─────────────────────────────────────────

class MalKabulIrsaliyeOlusturRequestDTO(BaseModel):
    """Yeni mal kabul irsaliyesi oluşturma isteği."""

    tedarikci_id: int = Field(..., gt=0)
    depo_id: int = Field(..., gt=0)
    tarih: date
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    kalemler: List[MalKabulKalemiOlusturDTO] = Field(default_factory=list)


class MalKabulIrsaliyeGuncelleRequestDTO(BaseModel):
    """Güncelleme isteği — tüm alanlar opsiyonel."""

    tedarikci_id: Optional[int] = Field(None, gt=0)
    depo_id: Optional[int] = Field(None, gt=0)
    tarih: Optional[date] = None
    tir_plaka: Optional[str] = Field(None, max_length=20)
    sofor_adi: Optional[str] = Field(None, max_length=100)
    durum: Optional[str] = Field(None, max_length=20)
    kalemler: Optional[List[MalKabulKalemiOlusturDTO]] = None

    @field_validator("durum")
    @classmethod
    def gecerli_durum(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in _IZINLI_DURUMLAR:
            raise ValueError(f"Geçersiz durum: '{v}'. İzin verilen: {_IZINLI_DURUMLAR}")
        return v


# ─────────────────────────────────────────
# İRSALİYE RESPONSE DTO'LARI
# ─────────────────────────────────────────

class MalKabulIrsaliyeResponseDTO(BaseModel):
    """Mal kabul irsaliyesi response."""

    id: int
    irsaliye_no: str
    tedarikci_id: int
    depo_id: int
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: str
    tarih: Optional[date] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    kalemler: List[MalKabulKalemiResponseDTO] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity) -> "MalKabulIrsaliyeResponseDTO":
        return cls(
            id=entity.id,
            irsaliye_no=entity.irsaliye_no,
            tedarikci_id=entity.tedarikci_id,
            depo_id=entity.depo_id,
            tir_plaka=entity.tir_plaka,
            sofor_adi=entity.sofor_adi,
            durum=entity.durum,
            tarih=entity.tarih,
            olusturma_tarihi=entity.olusturma_tarihi,
            guncelleme_tarihi=entity.guncelleme_tarihi,
            kalemler=[MalKabulKalemiResponseDTO.from_entity(k) for k in entity.kalemler],
        )
