"""Etiket Şablonu domain entity.

Palet etiketleri için ZPL + HTML template tutar. Placeholder'lar
({palet_no}, {lot_no}, {urun_isim}, {skt}, {koli}, {vardiya},
{uretim_tarihi}, {barkod}, {qr}) render aşamasında doldurulur.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class EtiketSablonu:
    id: Optional[int] = None
    ad: str = ""
    boyut: Optional[str] = None  # ör. "100x150mm"
    zpl_template: str = ""
    html_template: str = ""
    default_mi: bool = False
    aktif: bool = True
    olusturan_id: Optional[int] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    def dogrula(self) -> None:
        if not self.ad.strip():
            raise ValueError("Şablon adı boş olamaz.")
        if not self.zpl_template.strip():
            raise ValueError("ZPL template boş olamaz.")
        if not self.html_template.strip():
            raise ValueError("HTML template boş olamaz.")
