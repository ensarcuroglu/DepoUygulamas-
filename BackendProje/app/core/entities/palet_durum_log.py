from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class PaletDurumLog:
    """Üretim paleti durum geçiş logu — saf domain entity."""

    palet_id: int
    yeni_durum: str
    eski_durum: Optional[str] = None
    degistiren_kullanici_id: Optional[int] = None
    sebep: Optional[str] = None
    degisim_tarihi: datetime = field(default_factory=datetime.utcnow)
    id: Optional[int] = None
