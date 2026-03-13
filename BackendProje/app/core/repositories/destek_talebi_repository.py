from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.destek_talebi import DestekTalebi


class IDestekTalebiRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        kullanici_id: Optional[int] = None,
        durum: Optional[str] = None,
    ) -> List[DestekTalebi]:
        ...

    @abstractmethod
    def getir_id_ile(self, talep_id: int) -> Optional[DestekTalebi]:
        ...

    @abstractmethod
    def olustur(self, talep: DestekTalebi) -> DestekTalebi:
        ...

    @abstractmethod
    def guncelle(self, talep: DestekTalebi) -> DestekTalebi:
        ...
