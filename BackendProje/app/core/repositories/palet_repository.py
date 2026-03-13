from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.palet import Palet


class IPaletRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        lot_id: Optional[int] = None,
        raf_id: Optional[int] = None,
        sadece_aktif: bool = True,
    ) -> List[Palet]:
        ...

    @abstractmethod
    def getir_id_ile(self, palet_id: int) -> Optional[Palet]:
        ...

    @abstractmethod
    def getir_palet_no_ile(self, palet_no: str) -> Optional[Palet]:
        ...

    @abstractmethod
    def olustur(self, palet: Palet) -> Palet:
        ...

    @abstractmethod
    def guncelle(self, palet: Palet) -> Palet:
        ...

    @abstractmethod
    def sil(self, palet_id: int) -> bool:
        ...

    @abstractmethod
    def sonraki_palet_no(self) -> str:
        """Otomatik palet numarası üretir."""
        ...

    @abstractmethod
    def getir_fifo_sirayla(self, urun_id: int) -> List[Palet]:
        """FIFO sıralamasıyla (SKT asc, üretim tarihi asc, tarih asc)
        aktif paletleri döner. Stok çıkışında kullanılır."""
        ...
