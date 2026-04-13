from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.lot import Lot


class ILotRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        urun_id: Optional[int] = None, sadece_aktif: bool = True,
    ) -> List[Lot]:
        ...

    @abstractmethod
    def say(self, urun_id: Optional[int] = None, sadece_aktif: bool = True) -> int:
        ...

    @abstractmethod
    def getir_id_ile(self, lot_id: int) -> Optional[Lot]:
        ...

    @abstractmethod
    def getir_lot_no_ile(self, lot_no: str) -> Optional[Lot]:
        ...

    @abstractmethod
    def olustur(self, lot: Lot, auto_commit: bool = True) -> Lot:
        ...

    @abstractmethod
    def guncelle(self, lot: Lot, auto_commit: bool = True) -> Lot:
        ...

    @abstractmethod
    def sil(self, lot_id: int, auto_commit: bool = True) -> bool:
        ...

    @abstractmethod
    def getir_skt_yaklasan(self, gun: int = 30) -> List[Lot]:
        """Son kullanma tarihi yaklaşan aktif lotları döner."""
        ...
