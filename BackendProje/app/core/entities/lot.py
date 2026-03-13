from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


@dataclass
class Lot:
    """Lot / Parti takibi domain entity."""

    id: Optional[int] = None
    urun_id: int = 0
    lot_no: Optional[str] = None
    parti_no: Optional[str] = None
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    aciklama: str = ""
    aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def kapat(self) -> None:
        """Lotu kapatır (aktif=False)."""
        self.aktif = False

    def ac(self) -> None:
        """Kapatılmış lotu tekrar açar."""
        self.aktif = True

    def skt_gecmis_mi(self, referans_tarih: Optional[date] = None) -> bool:
        """Son kullanma tarihi geçmiş mi kontrol eder."""
        if self.son_kullanma_tarihi is None:
            return False
        referans = referans_tarih or date.today()
        return self.son_kullanma_tarihi < referans

    def skt_yaklasik_mi(self, gun: int = 30, referans_tarih: Optional[date] = None) -> bool:
        """Son kullanma tarihine belirtilen gün kadar kaldıysa True döner."""
        if self.son_kullanma_tarihi is None:
            return False
        referans = referans_tarih or date.today()
        from datetime import timedelta
        return referans <= self.son_kullanma_tarihi <= referans + timedelta(days=gun)
