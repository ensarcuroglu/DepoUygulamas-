from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.stok_sayim import StokSayim, StokSayimKalemi


class IStokSayimRepository(ABC):

    @abstractmethod
    def getir_hepsi(self, skip: int = 0, limit: int = 100) -> List[StokSayim]:
        ...

    @abstractmethod
    def getir_id_ile(self, sayim_id: int) -> Optional[StokSayim]:
        """Kalemleriyle birlikte getirir."""
        ...

    @abstractmethod
    def olustur(self, sayim: StokSayim) -> StokSayim:
        ...

    @abstractmethod
    def guncelle(self, sayim: StokSayim) -> StokSayim:
        ...

    @abstractmethod
    def kalem_ekle(self, kalem: StokSayimKalemi) -> StokSayimKalemi:
        ...

    @abstractmethod
    def kalem_guncelle(self, kalem: StokSayimKalemi) -> StokSayimKalemi:
        ...
