"""
Yerleştirme Görevi veri transfer nesneleri (DTO).
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from app.core.entities.yerlestirme_gorevi import GorevTipi, GorevDurum, YerlestirmeGorevi


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class YerlestirmeGoreviOlusturRequestDTO(BaseModel):
    palet_id: int = Field(..., gt=0)
    mal_kabul_irsaliye_id: Optional[int] = Field(None, gt=0)
    tip: str = Field(default=GorevTipi.YERLESTIRME)
    kaynak_raf_id: Optional[int] = Field(None, gt=0)
    onerilen_raf_id: int = Field(..., gt=0)
    oncelik: int = Field(default=5, ge=1, le=5, description="1=Acil, 5=Normal")

    @field_validator("tip")
    @classmethod
    def gecerli_tip(cls, v: str) -> str:
        if not GorevTipi.gecerli_mi(v):
            raise ValueError(f"Geçersiz görev tipi: '{v}'")
        return v


class YerlestirmeGoreviTamamlaRequestDTO(BaseModel):
    gerceklesen_raf_id: int = Field(..., gt=0, description="Operatörün barkod okuttuğu raf")


class YerlestirmeGoreviOverrideRequestDTO(BaseModel):
    gerceklesen_raf_id: int = Field(..., gt=0)
    neden: str = Field(..., min_length=5, max_length=500, description="Override gerekçesi")


class YerlestirmeGoreviIptalRequestDTO(BaseModel):
    neden: str = Field(..., min_length=1, max_length=500)


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class YerlestirmeGoreviResponseDTO(BaseModel):
    id: int
    palet_id: int
    mal_kabul_irsaliye_id: Optional[int]
    tip: str
    kaynak_raf_id: Optional[int]
    onerilen_raf_id: int
    gerceklesen_raf_id: Optional[int]
    durum: str
    oncelik: int
    atanan_kullanici_id: Optional[int]
    override_kullanici_id: Optional[int]
    override_neden: Optional[str]
    olusturma_tarihi: datetime
    baslama_tarihi: Optional[datetime]
    tamamlanma_tarihi: Optional[datetime]
    iptal_nedeni: Optional[str]
    onerilen_raf_farkli: bool

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, entity: YerlestirmeGorevi) -> "YerlestirmeGoreviResponseDTO":
        return cls(
            id=entity.id,
            palet_id=entity.palet_id,
            mal_kabul_irsaliye_id=entity.mal_kabul_irsaliye_id,
            tip=entity.tip,
            kaynak_raf_id=entity.kaynak_raf_id,
            onerilen_raf_id=entity.onerilen_raf_id,
            gerceklesen_raf_id=entity.gerceklesen_raf_id,
            durum=entity.durum,
            oncelik=entity.oncelik,
            atanan_kullanici_id=entity.atanan_kullanici_id,
            override_kullanici_id=entity.override_kullanici_id,
            override_neden=entity.override_neden,
            olusturma_tarihi=entity.olusturma_tarihi,
            baslama_tarihi=entity.baslama_tarihi,
            tamamlanma_tarihi=entity.tamamlanma_tarihi,
            iptal_nedeni=entity.iptal_nedeni,
            onerilen_raf_farkli=entity.onerilen_raf_farkli_mi(),
        )
