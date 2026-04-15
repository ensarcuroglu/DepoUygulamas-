"""
Palet Rezervasyonu veri transfer nesneleri.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class RezervasyonIptalRequestDTO(BaseModel):
    neden: Optional[str] = Field(None, max_length=500)


class RezervasyonDegistirRequestDTO(BaseModel):
    """Mevcut rezervasyonu iptal edip yeni palete yeniden rezervasyon atar."""
    yeni_palet_id: int = Field(..., gt=0)
    neden: Optional[str] = Field(None, max_length=500, description="Değişiklik gerekçesi")


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class PaletRezervasyonuResponseDTO(BaseModel):
    id: int
    palet_id: int
    siparis_id: int
    sevkiyat_kalemi_id: Optional[int]
    durum: str
    rezerve_tarihi: datetime
    kesinlesme_tarihi: Optional[datetime]
    iptal_tarihi: Optional[datetime]
    iptal_nedeni: Optional[str]

    # Zenginleştirilmiş alanlar
    palet_no: Optional[str] = None
    lot_no: Optional[str] = None
    urun_adi: Optional[str] = None
    siparis_no: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, e) -> "PaletRezervasyonuResponseDTO":
        from app.core.entities.palet_rezervasyonu import PaletRezervasyonu
        if not isinstance(e, PaletRezervasyonu):
            raise TypeError(f"Beklenen tip PaletRezervasyonu, gelen: {type(e)}")
        return cls(
            id=e.id,
            palet_id=e.palet_id,
            siparis_id=e.siparis_id,
            sevkiyat_kalemi_id=e.sevkiyat_kalemi_id,
            durum=e.durum,
            rezerve_tarihi=e.rezerve_tarihi,
            kesinlesme_tarihi=e.kesinlesme_tarihi,
            iptal_tarihi=e.iptal_tarihi,
            iptal_nedeni=e.iptal_nedeni,
            palet_no=e.palet_no,
            lot_no=e.lot_no,
            urun_adi=e.urun_adi,
            siparis_no=e.siparis_no,
        )


class StokDetayResponseDTO(BaseModel):
    """Ürün bazlı stok görünürlük özeti."""
    urun_id: int
    toplam_stok: int
    rezerve_stok: int
    uygun_stok: int
