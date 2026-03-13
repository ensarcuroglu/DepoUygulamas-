from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Palet:
    """Palet domain entity."""

    id: Optional[int] = None
    lot_id: int = 0
    raf_id: Optional[int] = None
    palet_no: str = ""
    koli_adedi: int = 0
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None
    tarih: datetime = field(default_factory=datetime.utcnow)
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def stok_dus(self, miktar: int) -> int:
        """Paletten belirtilen miktarda koli düşer.

        Returns:
            Düşürülen gerçek miktar (palet koli_adedi < miktar ise tamamını düşer).
        """
        if miktar <= 0:
            raise ValueError("Düşülecek miktar pozitif olmalı.")

        if self.koli_adedi <= miktar:
            dusurulen = self.koli_adedi
            self.koli_adedi = 0
            self.aktif = False
            return dusurulen
        else:
            self.koli_adedi -= miktar
            return miktar

    def sevk_et(self) -> None:
        """Paletin tamamını sevk eder (deaktif eder)."""
        self.koli_adedi = 0
        self.aktif = False

    def bos_mu(self) -> bool:
        return self.koli_adedi <= 0

    def raf_ata(self, raf_id: int) -> None:
        """Paleti bir rafa atar."""
        self.raf_id = raf_id
