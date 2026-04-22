from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.palet_etiket import PaletEtiket


class IPaletEtiketRepository(ABC):

    @abstractmethod
    def getir_hepsi_palet_id_ile(self, palet_id: int) -> List[PaletEtiket]:
        ...

    @abstractmethod
    def getir_id_ile(self, etiket_id: int) -> Optional[PaletEtiket]:
        ...

    @abstractmethod
    def olustur(self, etiket: PaletEtiket) -> PaletEtiket:
        ...

    @abstractmethod
    def guncelle(self, etiket: PaletEtiket) -> Optional[PaletEtiket]:
        ...
