from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Kategori:
    """Kategori domain entity."""

    id: Optional[int] = None
    isim: str = ""
    aciklama: str = ""
    ikon: str = "FolderOpen"
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def deaktif_et(self) -> None:
        self.aktif = False

    def aktif_et(self) -> None:
        self.aktif = True

    def isim_guncelle(self, yeni_isim: str) -> None:
        if not yeni_isim or not yeni_isim.strip():
            raise ValueError("Kategori ismi boş olamaz.")
        self.isim = yeni_isim.strip()
