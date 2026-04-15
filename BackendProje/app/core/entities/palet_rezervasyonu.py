from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from app.core.exceptions import GecersizDurumGecisiError


class RezervasyonDurum:
    AKTIF = "Aktif"
    KESINLESTI = "Kesinlesti"
    IPTAL_EDILDI = "IptalEdildi"

    _GECISLER: dict[str, set[str]] = {}

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


RezervasyonDurum._GECISLER = {
    RezervasyonDurum.AKTIF: {
        RezervasyonDurum.KESINLESTI,
        RezervasyonDurum.IPTAL_EDILDI,
    },
    RezervasyonDurum.KESINLESTI: set(),
    RezervasyonDurum.IPTAL_EDILDI: set(),
}


@dataclass
class PaletRezervasyonu:
    """Palet rezervasyonu domain entity.

    Sipariş Hazırlanıyor → Aktif rezervasyon oluşur.
    Sevkiyat tamamlandığında → Kesinlesti.
    Sipariş iptal veya palet değişiminde → IptalEdildi.
    """

    id: Optional[int] = None
    palet_id: int = 0
    siparis_id: int = 0
    sevkiyat_kalemi_id: Optional[int] = None
    durum: str = RezervasyonDurum.AKTIF
    rezerve_tarihi: datetime = field(default_factory=datetime.utcnow)
    kesinlesme_tarihi: Optional[datetime] = None
    iptal_tarihi: Optional[datetime] = None
    iptal_nedeni: Optional[str] = None

    # Görüntüleme alanları
    palet_no: Optional[str] = None
    lot_no: Optional[str] = None
    urun_adi: Optional[str] = None
    siparis_no: Optional[str] = None

    # ── İş Kuralları ──

    def _durum_gecisi(self, hedef: str) -> None:
        if not RezervasyonDurum.gecis_gecerli_mi(self.durum, hedef):
            raise GecersizDurumGecisiError(
                f"Rezervasyon için geçersiz durum geçişi: {self.durum} → {hedef}",
                mevcut=self.durum,
                hedef=hedef,
            )
        self.durum = hedef

    def iptal_et(self, neden: Optional[str] = None) -> None:
        """Rezervasyonu iptal eder; paleti serbest bırakır."""
        self._durum_gecisi(RezervasyonDurum.IPTAL_EDILDI)
        self.iptal_tarihi = datetime.utcnow()
        self.iptal_nedeni = neden

    def kesinlestir(self) -> None:
        """Sevkiyat tamamlandığında rezervasyonu kesinleştirir."""
        self._durum_gecisi(RezervasyonDurum.KESINLESTI)
        self.kesinlesme_tarihi = datetime.utcnow()
