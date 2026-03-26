from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.mal_kabul_irsaliye import MalKabulIrsaliye, MalKabulKalemi


class IMalKabulIrsaliyeRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
        depo_id: Optional[int] = None,
        tedarikci_id: Optional[int] = None,
    ) -> List[MalKabulIrsaliye]:
        ...

    @abstractmethod
    def getir_id_ile(self, irsaliye_id: int) -> Optional[MalKabulIrsaliye]:
        ...

    @abstractmethod
    def olustur(self, irsaliye: MalKabulIrsaliye) -> MalKabulIrsaliye:
        ...

    @abstractmethod
    def guncelle(self, irsaliye: MalKabulIrsaliye, auto_commit: bool = True) -> MalKabulIrsaliye:
        ...

    @abstractmethod
    def sil(self, irsaliye_id: int) -> bool:
        ...

    @abstractmethod
    def sonraki_irsaliye_no(self) -> str:
        """MKI-YYYY-NNNNN formatında numara üretir."""
        ...

    @abstractmethod
    def getir_kalem_palet_no_ile(self, palet_no: str) -> Optional[MalKabulKalemi]:
        """Palet numarasına göre kalem bulur (Faz 1b'de kullanılacak)."""
        ...
