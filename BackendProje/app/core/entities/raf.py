from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Raf:
    """Raf (shelf/rack) domain entity."""

    id: Optional[int] = None
    depo_id: Optional[int] = None
    kod: str = ""
    bolge: str = ""
    kapasite: int = 100
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def deaktif_et(self) -> None:
        self.aktif = False

    def aktif_et(self) -> None:
        self.aktif = True

    def kapasite_yeterli_mi(self, mevcut_palet_sayisi: int) -> bool:
        """Rafta yeni palet için yer olup olmadığını kontrol eder."""
        return mevcut_palet_sayisi < self.kapasite
