from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.yerlestirme_gorevi import YerlestirmeGorevi


class IYerlestirmeGoreviRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        atanan_kullanici_id: Optional[int] = None,
        palet_id: Optional[int] = None,
    ) -> List[YerlestirmeGorevi]:
        ...

    @abstractmethod
    def getir_id_ile(self, gorev_id: int) -> Optional[YerlestirmeGorevi]:
        ...

    @abstractmethod
    def olustur(self, gorev: YerlestirmeGorevi, auto_commit: bool = True) -> YerlestirmeGorevi:
        ...

    @abstractmethod
    def guncelle(self, gorev: YerlestirmeGorevi, auto_commit: bool = True) -> YerlestirmeGorevi:
        ...

    @abstractmethod
    def sonraki_gorevi_kilitle(
        self, kullanici_id: int
    ) -> Optional[YerlestirmeGorevi]:
        """Pull-based FIFO: öncelik ASC, olusturma_tarihi ASC sırasıyla
        ilk BEKLIYOR görevi SELECT FOR UPDATE ile kilitler ve ATANDI yapar."""
        ...
