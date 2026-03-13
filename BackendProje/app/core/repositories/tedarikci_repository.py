from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.tedarikci import Tedarikci


class ITedarikciRepository(ABC):

    @abstractmethod
    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Tedarikci]:
        ...

    @abstractmethod
    def getir_id_ile(self, tedarikci_id: int) -> Optional[Tedarikci]:
        ...

    @abstractmethod
    def olustur(self, tedarikci: Tedarikci) -> Tedarikci:
        ...

    @abstractmethod
    def guncelle(self, tedarikci: Tedarikci) -> Tedarikci:
        ...

    @abstractmethod
    def sil(self, tedarikci_id: int) -> bool:
        ...
