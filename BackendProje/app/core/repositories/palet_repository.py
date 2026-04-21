from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.palet import Palet


class IPaletRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        lot_id: Optional[int] = None,
        raf_id: Optional[int] = None,
        ean: Optional[str] = None,
        sadece_aktif: bool = True,
        kaynak: Optional[str] = None,
        durum: Optional[str] = None,
    ) -> List[Palet]:
        ...

    @abstractmethod
    def getir_id_ile(self, palet_id: int) -> Optional[Palet]:
        ...

    @abstractmethod
    def getir_palet_no_ile(self, palet_no: str, kilitli_mi: bool = False) -> Optional[Palet]:
        """Palet numarasına göre paleti getirir. Eşzamanlı işlemlerde kilit (FOR UPDATE) kullanılabilir."""
        ...

    @abstractmethod
    def olustur(self, palet: Palet, auto_commit: bool = True) -> Palet:
        ...

    @abstractmethod
    def guncelle(self, palet: Palet, auto_commit: bool = True) -> Palet:
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

    @abstractmethod
    def getir_fifo_sirayla_kilitli(self, urun_id: int) -> List[Palet]:
        """FIFO sıralamasıyla aktif paletleri SELECT FOR UPDATE ile kilitleyerek döner.
        Eşzamanlı çıkış isteklerinde race condition engellenir."""
        ...
