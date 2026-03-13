from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.depo import Depo


class IDepoRepository(ABC):

    @abstractmethod
    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Depo]:
        ...

    @abstractmethod
    def getir_id_ile(self, depo_id: int) -> Optional[Depo]:
        ...

    @abstractmethod
    def olustur(self, depo: Depo) -> Depo:
        ...

    @abstractmethod
    def guncelle(self, depo: Depo) -> Depo:
        ...

    @abstractmethod
    def sil(self, depo_id: int) -> bool:
        ...
