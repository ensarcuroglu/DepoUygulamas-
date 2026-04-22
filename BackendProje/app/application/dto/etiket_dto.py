"""Etiket şablonu ve palet etiket DTO'ları."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.entities.etiket_sablonu import EtiketSablonu
from app.core.entities.palet_etiket import PaletEtiket


# ── EtiketSablonu ─────────────────────────────────────────────────────────────

class EtiketSablonuOlusturDTO(BaseModel):
    ad: str = Field(min_length=1, max_length=100)
    boyut: Optional[str] = Field(default=None, max_length=30)
    zpl_template: str = Field(min_length=1)
    html_template: str = Field(min_length=1)
    default_mi: bool = False
    aktif: bool = True


class EtiketSablonuGuncelleDTO(BaseModel):
    ad: Optional[str] = Field(default=None, min_length=1, max_length=100)
    boyut: Optional[str] = Field(default=None, max_length=30)
    zpl_template: Optional[str] = Field(default=None, min_length=1)
    html_template: Optional[str] = Field(default=None, min_length=1)
    default_mi: Optional[bool] = None
    aktif: Optional[bool] = None


class EtiketSablonuResponseDTO(BaseModel):
    id: Optional[int]
    ad: str
    boyut: Optional[str]
    zpl_template: str
    html_template: str
    default_mi: bool
    aktif: bool
    olusturan_id: Optional[int]
    olusturma_tarihi: datetime

    @classmethod
    def from_entity(cls, s: EtiketSablonu) -> "EtiketSablonuResponseDTO":
        return cls(
            id=s.id, ad=s.ad, boyut=s.boyut,
            zpl_template=s.zpl_template, html_template=s.html_template,
            default_mi=s.default_mi, aktif=s.aktif,
            olusturan_id=s.olusturan_id, olusturma_tarihi=s.olusturma_tarihi,
        )


# ── PaletEtiket ──────────────────────────────────────────────────────────────

class PaletEtiketOlusturDTO(BaseModel):
    sablon_id: int = Field(gt=0)


class PaletEtiketResponseDTO(BaseModel):
    id: Optional[int]
    palet_id: int
    sablon_id: int
    sablon_ad: Optional[str] = None
    palet_no: Optional[str] = None
    render_edilmis_zpl: str
    render_edilmis_html: str
    barkod_deger: str
    qr_deger: Optional[str]
    basim_sayisi: int
    son_basim_tarihi: Optional[datetime]
    kullanici_id: Optional[int]
    olusturma_tarihi: datetime

    @classmethod
    def from_entity(cls, e: PaletEtiket) -> "PaletEtiketResponseDTO":
        return cls(
            id=e.id, palet_id=e.palet_id, sablon_id=e.sablon_id,
            sablon_ad=e.sablon_ad, palet_no=e.palet_no,
            render_edilmis_zpl=e.render_edilmis_zpl,
            render_edilmis_html=e.render_edilmis_html,
            barkod_deger=e.barkod_deger, qr_deger=e.qr_deger,
            basim_sayisi=e.basim_sayisi, son_basim_tarihi=e.son_basim_tarihi,
            kullanici_id=e.kullanici_id, olusturma_tarihi=e.olusturma_tarihi,
        )
