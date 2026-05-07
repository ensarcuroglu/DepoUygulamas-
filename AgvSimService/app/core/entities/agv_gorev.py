"""AGV görev — WMS görevinin AGV içi temsilcisi."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class AgvGorev:
    """WMS'ten gelen bir taşıma görevinin AGV simülasyonundaki kaydı.

    `wms_gorev_id` ve `wms_gorev_tipi` WMS callback'inde geri gönderilir.
    """

    gorev_id: str                       # AGV iç id (uuid kısa)
    wms_gorev_id: int                   # WMS YerlestirmeGorevi.id veya ToplamaGorevi.id
    wms_gorev_tipi: str                 # "Yerlestirme" | "Toplama"
    kaynak_raf_id: int
    hedef_raf_id: int
    palet_id: Optional[int] = None
    oncelik: int = 5                    # 1=Acil … 5=Normal
    olusturma_ts: datetime = field(default_factory=datetime.utcnow)
    baslama_tick: Optional[int] = None
    tamamlanma_tick: Optional[int] = None
