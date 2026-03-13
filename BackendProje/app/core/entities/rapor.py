from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, List


class RaporTur:
    STOK = "stok"
    SIPARIS = "siparis"
    FINANSAL = "finansal"
    PERFORMANS = "performans"


class RaporFormat:
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class RaporPeriyod:
    GUNLUK = "gunluk"
    HAFTALIK = "haftalik"
    AYLIK = "aylik"


@dataclass
class RaporSablonu:
    """Rapor şablonu domain entity."""

    id: Optional[int] = None
    ad: str = ""
    tur: str = RaporTur.STOK
    aciklama: str = ""
    config: Optional[Any] = None
    olusturan_kullanici_id: Optional[int] = None
    is_aktif: bool = True
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)

    def deaktif_et(self) -> None:
        self.is_aktif = False
        self.guncelleme_tarihi = datetime.utcnow()


@dataclass
class RaporLogu:
    """Rapor çalıştırma logu domain entity."""

    id: Optional[int] = None
    sablon_id: Optional[int] = None
    kullanici_id: int = 0
    parametreler: Optional[Any] = None
    durum: str = "Basarili"
    hata_mesaji: Optional[str] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    tamamlanma_tarihi: Optional[datetime] = None

    def basarisiz_isaretle(self, hata: str) -> None:
        self.durum = "Hatali"
        self.hata_mesaji = hata
        self.tamamlanma_tarihi = datetime.utcnow()

    def basarili_isaretle(self) -> None:
        self.durum = "Basarili"
        self.tamamlanma_tarihi = datetime.utcnow()


@dataclass
class RaporSchedule:
    """Zamanlı rapor planlaması domain entity."""

    id: Optional[int] = None
    sablon_id: int = 0
    sablon_adi: str = ""
    periyod: str = RaporPeriyod.GUNLUK
    saat: str = "09:00"
    alici_emailler: Optional[List[str]] = None
    format: str = RaporFormat.PDF
    is_aktif: bool = True
    son_calistirilma: Optional[datetime] = None
    olusturma_tarihi: datetime = field(default_factory=datetime.utcnow)
    guncelleme_tarihi: datetime = field(default_factory=datetime.utcnow)

    def deaktif_et(self) -> None:
        self.is_aktif = False
        self.guncelleme_tarihi = datetime.utcnow()

    def calistirildi_isaretle(self) -> None:
        self.son_calistirilma = datetime.utcnow()
        self.guncelleme_tarihi = datetime.utcnow()
