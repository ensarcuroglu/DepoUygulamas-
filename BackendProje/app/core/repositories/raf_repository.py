from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.raf import Raf


class IRafRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        depo_id: Optional[int] = None,
        zon_id: Optional[int] = None,
        sadece_aktif: bool = True,
    ) -> List[Raf]:
        ...

    @abstractmethod
    def getir_id_ile(self, raf_id: int) -> Optional[Raf]:
        ...

    @abstractmethod
    def olustur(self, raf: Raf) -> Raf:
        ...

    @abstractmethod
    def guncelle(self, raf: Raf) -> Raf:
        ...

    @abstractmethod
    def getir_kod_ile(self, kod: str, depo_id: int) -> Optional[Raf]:
        """Depo içinde raf koduna göre arar (case-insensitive)."""
        ...

    @abstractmethod
    def sil(self, raf_id: int) -> bool:
        ...
