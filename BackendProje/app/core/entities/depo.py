from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Depo:
    """Depo (warehouse) domain entity."""

    id: Optional[int] = None
    isim: str = ""
    adres: str = ""
    aciklama: str = ""
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def deaktif_et(self) -> None:
        self.aktif = False

    def aktif_et(self) -> None:
        self.aktif = True
