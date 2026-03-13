from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.kullanici import Kullanici


class IKullaniciRepository(ABC):

    @abstractmethod
    def getir_hepsi(self, skip: int = 0, limit: int = 100) -> List[Kullanici]:
        ...

    @abstractmethod
    def getir_id_ile(self, kullanici_id: int) -> Optional[Kullanici]:
        ...

    @abstractmethod
    def getir_kullanici_adi_ile(self, kullanici_adi: str) -> Optional[Kullanici]:
        ...

    @abstractmethod
    def olustur(self, kullanici: Kullanici) -> Kullanici:
        ...

    @abstractmethod
    def guncelle(self, kullanici: Kullanici) -> Kullanici:
        ...

    @abstractmethod
    def sil(self, kullanici_id: int) -> bool:
        ...
