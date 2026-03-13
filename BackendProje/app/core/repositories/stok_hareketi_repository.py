from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.stok_hareketi import StokHareketi


class IStokHareketiRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        urun_id: Optional[int] = None,
        lot_id: Optional[int] = None,
        hareket_tipi: Optional[str] = None,
    ) -> List[StokHareketi]:
        ...

    @abstractmethod
    def olustur(self, hareket: StokHareketi) -> StokHareketi:
        ...
