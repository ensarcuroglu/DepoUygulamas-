from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class DashboardIstatistik:
    """Dashboard aggregate istatistikleri (domain value object)."""
    toplam_urun: int
    kritik_stok_sayisi: int
    bugunku_hareket: int
    toplam_deger: float


class IDashboardRepository(ABC):

    @abstractmethod
    def istatistik_getir(self) -> DashboardIstatistik:
        """Toplam ürün, kritik stok, günlük hareket ve envanter değeri döner."""
        ...
