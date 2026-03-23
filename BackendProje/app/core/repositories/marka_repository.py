from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.marka import Marka


class IMarkaRepository(ABC):

    @abstractmethod
    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Marka]:
        ...

    @abstractmethod
    def getir_id_ile(self, marka_id: int) -> Optional[Marka]:
        ...

    @abstractmethod
    def olustur(self, marka: Marka) -> Marka:
        ...

    @abstractmethod
    def guncelle(self, marka: Marka) -> Marka:
        ...

    @abstractmethod
    def getir_isim_ile(self, isim: str) -> Optional[Marka]:
        """İsme göre marka arar (case-insensitive)."""
        ...

    @abstractmethod
    def sil(self, marka_id: int) -> bool:
        """Soft delete — aktif=False yapar."""
        ...
