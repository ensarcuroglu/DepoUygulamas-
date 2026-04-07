from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


# ── Hafif nested bilgi yapıları (DTO zenginleştirme amaçlı) ──

@dataclass
class UrunBilgi:
    """Palet yanıtında taşınan minimal ürün bilgisi."""
    id: Optional[int] = None
    isim: str = ""
    ean: Optional[str] = None
    barkod: Optional[str] = None


@dataclass
class LotBilgi:
    """Palet yanıtında taşınan minimal lot bilgisi."""
    id: Optional[int] = None
    lot_no: Optional[str] = None
    urun_id: int = 0
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    urun: Optional[UrunBilgi] = None


@dataclass
class RafBilgi:
    """Palet yanıtında taşınan minimal raf bilgisi."""
    id: Optional[int] = None
    kod: str = ""
    bolge: str = ""


@dataclass
class Palet:
    """Palet domain entity."""

    id: Optional[int] = None
    lot_id: int = 0
    raf_id: int = 0  # migrate_putaway_system.py Adım 10 sonrası zorunlu
    palet_no: str = ""
    koli_adedi: int = 0
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None
    tarih: datetime = field(default_factory=datetime.utcnow)
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # Opsiyonel nested bilgi — mapper tarafından doldurulur
    lot: Optional[LotBilgi] = None
    raf: Optional[RafBilgi] = None

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
