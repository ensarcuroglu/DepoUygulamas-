from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.irsaliye import Irsaliye


class IIrsaliyeRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ) -> List[Irsaliye]:
        ...

    @abstractmethod
    def getir_id_ile(self, irsaliye_id: int) -> Optional[Irsaliye]:
        ...

    @abstractmethod
    def olustur(self, irsaliye: Irsaliye, auto_commit: bool = True) -> Irsaliye:
        ...

    @abstractmethod
    def guncelle(self, irsaliye: Irsaliye, auto_commit: bool = True) -> Irsaliye:
        ...

    @abstractmethod
    def sonraki_irsaliye_no(self) -> str:
        """IRS-YYYY-NNNN formatında numara üretir."""
        ...

    @abstractmethod
    def sevkiyat_icin_irsaliye_var_mi(self, sevkiyat_id: int) -> bool:
        """Belirtilen sevkiyata bağlı irsaliye olup olmadığını kontrol eder."""
        ...
