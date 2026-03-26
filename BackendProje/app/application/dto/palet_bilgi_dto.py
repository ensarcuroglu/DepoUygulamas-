"""Palet bilgi DTO — palet sorgulama response modeli.

IPaletVeriKaynagiService ve PaletBazliStokDomainService tarafindan kullanilir.
Kaynak bagimsiz: irsaliye, ERP veya sistem (DB) verisi ayni formatta doner.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel

PaletDurum = Literal["aktif", "pasif"]
PaletKaynak = Literal["irsaliye", "erp", "sistem"]


class PaletBilgiDTO(BaseModel):
    """Palet numarasina gore getirilen tum bilgileri icerir."""

    palet_no: str
    urun_id: int
    urun_adi: str
    urun_barkod: Optional[str] = None
    lot_no: Optional[str] = None
    lot_id: Optional[int] = None
    miktar: int  # koli_adedi
    raf_id: Optional[int] = None
    raf_bilgi: Optional[str] = None  # "Depo-A / R-03-B"
    depo_id: int
    depo_adi: str
    durum: PaletDurum
    kaynak: PaletKaynak
    son_kullanma_tarihi: Optional[date] = None
    giris_yapildi_mi: bool

    model_config = {"from_attributes": True}
