from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional


class IrsaliyeDurum:
    TASLAK = "Taslak"
    KESILDI = "Kesildi"
    GONDERILDI = "Gonderildi"


class BelgeTuru:
    SEVK_IRSALIYESI = "SevkIrsaliyesi"
    IADE_IRSALIYESI = "IadeIrsaliyesi"


@dataclass
class Irsaliye:
    """İrsaliye domain entity."""

    id: Optional[int] = None
    siparis_id: int = 0
    sevkiyat_id: Optional[int] = None
    irsaliye_no: str = ""
    irsaliye_tarihi: Optional[date] = None
    belge_turu: str = BelgeTuru.SEVK_IRSALIYESI
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: str = IrsaliyeDurum.TASLAK
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)

    # ── İş Kuralları ──

    def kes(self) -> None:
        """İrsaliyeyi kesildi olarak işaretler."""
        if self.durum != IrsaliyeDurum.TASLAK:
            raise ValueError("Sadece taslak durumundaki irsaliyeler kesilebilir.")
        self.durum = IrsaliyeDurum.KESILDI
        self.guncelleme_tarihi = datetime.utcnow()

    def gonder(self) -> None:
        """İrsaliyeyi gönderildi olarak işaretler."""
        if self.durum != IrsaliyeDurum.KESILDI:
            raise ValueError("Sadece kesilmiş irsaliyeler gönderilebilir.")
        self.durum = IrsaliyeDurum.GONDERILDI
        self.guncelleme_tarihi = datetime.utcnow()

    def duzenlenebilir_mi(self) -> bool:
        """Sadece taslak irsaliyeler düzenlenebilir."""
        return self.durum == IrsaliyeDurum.TASLAK
