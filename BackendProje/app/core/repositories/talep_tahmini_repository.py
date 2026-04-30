from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class TalepTahminUrunKaydi:
    id: int
    isim: str
    barkod: Optional[str]
    min_stok: int
    stok_miktari: int
    kategori_id: Optional[int] = None
    marka_id: Optional[int] = None


@dataclass(frozen=True)
class GunlukCikisKaydi:
    tarih: date
    miktar: float


class ITalepTahminiRepository(ABC):
    @abstractmethod
    def urunleri_listele(
        self,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> list[TalepTahminUrunKaydi]:
        ...

    @abstractmethod
    def urun_getir(self, urun_id: int) -> Optional[TalepTahminUrunKaydi]:
        ...

    @abstractmethod
    def gunluk_cikislari_getir(
        self,
        urun_id: int,
        baslangic: date,
        bitis: date,
    ) -> list[GunlukCikisKaydi]:
        ...

    @abstractmethod
    def aktif_urun_idleri(self) -> list[int]:
        """Tum aktif urun id listesi (nightly job icin)."""
        ...

    @abstractmethod
    def kategori_gunluk_medyan(self, kategori_id: int) -> Optional[float]:
        """Cold-start fallback icin kategori bazli gunluk talep medyani."""
        ...

    @abstractmethod
    def marka_gunluk_medyan(self, marka_id: int) -> Optional[float]:
        """Cold-start fallback icin marka bazli gunluk talep medyani."""
        ...


@dataclass(frozen=True)
class CacheKaydi:
    urun_id: int
    tahmin_gun: int
    payload: dict
    stok_riski: str
    tahmini_talep: float
    onerilen_ikmal: float
    veri_guven_skoru: float
    model_versiyonu: str
    hesaplanma_tarihi: date


class ITalepTahminCacheRepository(ABC):
    """Nightly precompute icin tahmin cache erisimi."""

    @abstractmethod
    def yaz(self, kayit: CacheKaydi) -> None:
        ...

    @abstractmethod
    def getir(self, urun_id: int, tahmin_gun: int) -> Optional[CacheKaydi]:
        ...

    @abstractmethod
    def riskli_urunler(
        self,
        tahmin_gun: int,
        risk_seviyeleri: tuple[str, ...] = ("kritik", "dikkat"),
        limit: int = 50,
    ) -> list[CacheKaydi]:
        ...

    @abstractmethod
    def temizle(self, gun_oncesi: int = 7) -> int:
        """Belirli tarihten eski kayitlari sil."""
        ...
