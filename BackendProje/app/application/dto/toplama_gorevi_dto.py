"""
Toplama Görevi (Pick Task) veri transfer nesneleri.
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────
# İSTEK (REQUEST) DTO'LARI
# ─────────────────────────────────────────

class PickTaskUretRequestDTO(BaseModel):
    """Sevkiyattan toplama görevi üretme isteği."""
    sevkiyat_id: int = Field(..., gt=0)


class SiradanGorevAlRequestDTO(BaseModel):
    """Operatörün sıradaki görevi havuzdan çekme isteği."""
    depo_id: Optional[int] = Field(None, gt=0)


class GorevTamamlaRequestDTO(BaseModel):
    """Görev tamamlama isteği (tam toplama zorunlu)."""
    pass  # MVP: tam koli zorunlu, ek input gerekmez


class GorevIptalRequestDTO(BaseModel):
    """Görev iptal isteği."""
    neden: Optional[str] = Field(None, max_length=500)


class FefoOverrideRequestDTO(BaseModel):
    """Admin FEFO override isteği — mevcut göreve farklı palet atar."""
    yeni_palet_id: int = Field(..., gt=0)
    override_neden: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Override gerekçesi (en az 10 karakter zorunlu)",
    )


# ─────────────────────────────────────────
# YANIT (RESPONSE) DTO'LARI
# ─────────────────────────────────────────

class ToplamaGoreviResponseDTO(BaseModel):
    id: int
    sevkiyat_id: int
    palet_id: int
    lot_id: int
    urun_id: int
    depo_id: Optional[int]
    atanan_kullanici_id: Optional[int]
    durum: str
    fefo_override: bool
    override_neden: Optional[str]
    override_kullanici_id: Optional[int]
    sira_no: int
    olusturma_tarihi: datetime
    atanma_tarihi: Optional[datetime]
    baslama_tarihi: Optional[datetime]
    tamamlanma_tarihi: Optional[datetime]
    iptal_nedeni: Optional[str]

    # Zenginleştirilmiş alanlar
    palet_no: Optional[str] = None
    urun_adi: Optional[str] = None
    lot_no: Optional[str] = None
    koli_adedi: Optional[int] = None
    atanan_kullanici_adi: Optional[str] = None

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, e) -> "ToplamaGoreviResponseDTO":
        from app.core.entities.toplama_gorevi import ToplamaGorevi
        assert isinstance(e, ToplamaGorevi)
        return cls(
            id=e.id,
            sevkiyat_id=e.sevkiyat_id,
            palet_id=e.palet_id,
            lot_id=e.lot_id,
            urun_id=e.urun_id,
            depo_id=e.depo_id,
            atanan_kullanici_id=e.atanan_kullanici_id,
            durum=e.durum,
            fefo_override=e.fefo_override,
            override_neden=e.override_neden,
            override_kullanici_id=e.override_kullanici_id,
            sira_no=e.sira_no,
            olusturma_tarihi=e.olusturma_tarihi,
            atanma_tarihi=e.atanma_tarihi,
            baslama_tarihi=e.baslama_tarihi,
            tamamlanma_tarihi=e.tamamlanma_tarihi,
            iptal_nedeni=e.iptal_nedeni,
            palet_no=e.palet_no,
            urun_adi=e.urun_adi,
            lot_no=e.lot_no,
            koli_adedi=e.koli_adedi,
            atanan_kullanici_adi=e.atanan_kullanici_adi,
        )
