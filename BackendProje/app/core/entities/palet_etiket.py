"""Palet Etiket domain entity — bir şablondan render edilmiş palet etiketi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PaletEtiket:
    id: Optional[int] = None
    palet_id: int = 0
    sablon_id: int = 0
    render_edilmis_zpl: str = ""
    render_edilmis_html: str = ""
    barkod_deger: str = ""
    qr_deger: Optional[str] = None
    basim_sayisi: int = 0
    son_basim_tarihi: Optional[datetime] = None
    kullanici_id: Optional[int] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # Opsiyonel: yanıt zenginleştirme
    sablon_ad: Optional[str] = None
    palet_no: Optional[str] = None

    def basildi(self) -> None:
        self.basim_sayisi += 1
        self.son_basim_tarihi = datetime.utcnow()
