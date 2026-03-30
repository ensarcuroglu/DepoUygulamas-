from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.core.entities.sevkiyat_plani import SevkiyatPlani


class ISevkiyatPlaniRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        tarih_baslangic: Optional[date] = None,
        tarih_bitis: Optional[date] = None,
    ) -> List[SevkiyatPlani]:
        ...

    @abstractmethod
    def getir_id_ile(self, plan_id: int) -> Optional[SevkiyatPlani]:
        ...

    @abstractmethod
    def olustur(self, plan: SevkiyatPlani, auto_commit: bool = True) -> SevkiyatPlani:
        ...

    @abstractmethod
    def guncelle(self, plan: SevkiyatPlani, auto_commit: bool = True) -> SevkiyatPlani:
        ...

    @abstractmethod
    def getir_siparis_id_ile(self, siparis_id: int) -> Optional[SevkiyatPlani]:
        """Siparişe ait sevkiyat planını getirir (varsa)."""
        ...

    @abstractmethod
    def sil(self, plan_id: int, auto_commit: bool = True) -> bool:
        ...
