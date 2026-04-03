"""
Palet veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field

from app.core.entities.palet import Palet


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class PaletOlusturRequestDTO(BaseModel):
    lot_id: int = Field(..., gt=0, description="LOT ID")
    raf_id: Optional[int] = Field(None, gt=0, description="Raf ID")
    palet_no: str = Field(..., min_length=1, max_length=100)
    koli_adedi: int = Field(..., gt=0, description="Koli adedi pozitif olmalı")
    palet_kg: Optional[float] = Field(None, ge=0)
    vardiya: Optional[str] = Field(None, max_length=50)


class PaletGuncelleRequestDTO(BaseModel):
    raf_id: Optional[int] = Field(None, gt=0)
    koli_adedi: Optional[int] = Field(None, gt=0)
    palet_kg: Optional[float] = Field(None, ge=0)
    vardiya: Optional[str] = Field(None, max_length=50)
    aktif: Optional[bool] = None


# ─────────────────────────────────────────
# NESTED BİLGİ DTO'LARI
# ─────────────────────────────────────────

class UrunInfoDTO(BaseModel):
    """Palet yanıtında taşınan minimal ürün bilgisi."""
    id: Optional[int] = None
    isim: str = ""
    ean: Optional[str] = None
    barkod: Optional[str] = None

    model_config = {"from_attributes": True}


class LotInfoDTO(BaseModel):
    """Palet yanıtında taşınan minimal lot bilgisi."""
    id: Optional[int] = None
    lot_no: Optional[str] = None
    urun_id: int = 0
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    urun: Optional[UrunInfoDTO] = None

    model_config = {"from_attributes": True}


class RafInfoDTO(BaseModel):
    """Palet yanıtında taşınan minimal raf bilgisi."""
    id: Optional[int] = None
    kod: str = ""
    bolge: str = ""

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class PaletResponseDTO(BaseModel):
    id: int
    lot_id: int
    raf_id: Optional[int] = None
    palet_no: str
    koli_adedi: int
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None
    tarih: datetime
    aktif: bool
    olusturma_tarihi: datetime

    # Nested ilişkisel bilgiler
    lot: Optional[LotInfoDTO] = None
    raf: Optional[RafInfoDTO] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: Palet) -> "PaletResponseDTO":
        lot_dto = None
        if entity.lot:
            urun_dto = None
            if entity.lot.urun:
                urun_dto = UrunInfoDTO(
                    id=entity.lot.urun.id,
                    isim=entity.lot.urun.isim,
                    ean=entity.lot.urun.ean,
                    barkod=entity.lot.urun.barkod,
                )
            lot_dto = LotInfoDTO(
                id=entity.lot.id,
                lot_no=entity.lot.lot_no,
                urun_id=entity.lot.urun_id,
                uretim_tarihi=entity.lot.uretim_tarihi,
                son_kullanma_tarihi=entity.lot.son_kullanma_tarihi,
                urun=urun_dto,
            )

        raf_dto = None
        if entity.raf:
            raf_dto = RafInfoDTO(
                id=entity.raf.id,
                kod=entity.raf.kod,
                bolge=entity.raf.bolge,
            )

        return cls(
            id=entity.id,
            lot_id=entity.lot_id,
            raf_id=entity.raf_id,
            palet_no=entity.palet_no,
            koli_adedi=entity.koli_adedi,
            palet_kg=entity.palet_kg,
            vardiya=entity.vardiya,
            tarih=entity.tarih,
            aktif=entity.aktif,
            olusturma_tarihi=entity.olusturma_tarihi,
            lot=lot_dto,
            raf=raf_dto,
        )

