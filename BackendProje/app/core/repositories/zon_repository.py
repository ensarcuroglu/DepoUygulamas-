from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.zon import Zon


class IZonRepository(ABC):
    @abstractmethod
    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        depo_id: Optional[int] = None,
        tip: Optional[str] = None,
        sadece_aktif: bool = True,
    ) -> List[Zon]:
        ...

    @abstractmethod
    def getir_id_ile(self, zon_id: int) -> Optional[Zon]:
        ...

    @abstractmethod
    def getir_idler_ile(self, ids: List[int]) -> List[Zon]:
        """Verilen id listesindeki zonları tek seferde döner (sıra/aktiflik filtresi yok)."""
        ...

    @abstractmethod
    def getir_kod_ile(self, kod: str) -> Optional[Zon]:
        ...

    @abstractmethod
    def olustur(self, zon: Zon) -> Zon:
        ...

    @abstractmethod
    def guncelle(self, zon: Zon) -> Zon:
        ...

    @abstractmethod
    def sil(self, zon_id: int) -> bool:
        ...

