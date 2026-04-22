"""Üretim paleti giriş sistemi DTO'ları."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.core.entities.palet import Palet





class UretimPaletiOlusturRequestDTO(BaseModel):
    lot_id: int
    depo_id: int = Field(gt=0, description="Paletin oluşturulacağı hedef depo (zorunlu).")
    koli_adedi: int = Field(gt=0)
    uretim_tarihi: Optional[date] = None
    lot_no: Optional[str] = None
    palet_kg: Optional[float] = Field(default=None, gt=0)
    vardiya: Optional[str] = None
    # ── Endüstri standardı üretim meta alanları (opsiyonel) ──
    uretim_hatti: Optional[str] = Field(default=None, max_length=50)
    makine_kodu: Optional[str] = Field(default=None, max_length=50)
    operator_kullanici_id: Optional[int] = Field(default=None, gt=0)
    brut_kg: Optional[float] = Field(default=None, gt=0)
    net_kg: Optional[float] = Field(default=None, gt=0)


class UretimPaletiKabulRequestDTO(BaseModel):
    palet_no: str


class UretimPaletiKarantinaRequestDTO(BaseModel):
    palet_no: str
    sebep: Optional[str] = None


class UretimPaletiKarantinaCikarRequestDTO(BaseModel):
    palet_no: str
    sebep: Optional[str] = None


class UretimPaletiIptalRequestDTO(BaseModel):
    palet_no: str
    sebep: str = Field(min_length=1)


class UretimPaletiYerlestirRequestDTO(BaseModel):
    palet_no: str
    raf_id: int


class UretimPaletiResponseDTO(BaseModel):
    id: Optional[int]
    palet_no: str
    lot_id: int
    lot_no: Optional[str]
    koli_adedi: int
    palet_kg: Optional[float]
    vardiya: Optional[str]
    kaynak: Optional[str]
    durum: Optional[str]
    uretim_tarihi: Optional[date]
    kabul_eden_kullanici_id: Optional[int]
    kabul_tarihi: Optional[datetime]
    iptal_sebebi: Optional[str]
    aktif: bool
    olusturma_tarihi: datetime
    urun_isim: Optional[str] = None
    lot_skt: Optional[date] = None
    # ── Üretim meta alanları ──
    uretim_hatti: Optional[str] = None
    makine_kodu: Optional[str] = None
    operator_kullanici_id: Optional[int] = None
    brut_kg: Optional[float] = None
    net_kg: Optional[float] = None

    @classmethod
    def from_entity(cls, p: Palet) -> "UretimPaletiResponseDTO":
        urun_isim = None
        lot_skt = None
        if p.lot:
            lot_skt = p.lot.son_kullanma_tarihi
            if p.lot.urun:
                urun_isim = p.lot.urun.isim
        return cls(
            id=p.id,
            palet_no=p.palet_no,
            lot_id=p.lot_id,
            lot_no=p.lot_no,
            koli_adedi=p.koli_adedi,
            palet_kg=p.palet_kg,
            vardiya=p.vardiya,
            kaynak=p.kaynak,
            durum=p.durum,
            uretim_tarihi=p.uretim_tarihi,
            kabul_eden_kullanici_id=p.kabul_eden_kullanici_id,
            kabul_tarihi=p.kabul_tarihi,
            iptal_sebebi=p.iptal_sebebi,
            aktif=p.aktif,
            olusturma_tarihi=p.olusturma_tarihi,
            urun_isim=urun_isim,
            lot_skt=lot_skt,
            uretim_hatti=getattr(p, "uretim_hatti", None),
            makine_kodu=getattr(p, "makine_kodu", None),
            operator_kullanici_id=getattr(p, "operator_kullanici_id", None),
            brut_kg=getattr(p, "brut_kg", None),
            net_kg=getattr(p, "net_kg", None),
        )
