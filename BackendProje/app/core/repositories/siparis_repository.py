from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.siparis import Siparis


class ISiparisRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        durum: Optional[str] = None,
        arama: Optional[str] = None,
    ) -> List[Siparis]:
        ...

    @abstractmethod
    def getir_id_ile(self, siparis_id: int) -> Optional[Siparis]:
        """Kalemleriyle birlikte getirir."""
        ...

    @abstractmethod
    def olustur(self, siparis: Siparis) -> Siparis:
        ...

    @abstractmethod
    def guncelle(self, siparis: Siparis) -> Siparis:
        ...

    @abstractmethod
    def sil(self, siparis_id: int) -> bool:
        ...

    @abstractmethod
    def sonraki_siparis_no(self) -> str:
        """SIP-YYYY-NNNN formatında numara üretir."""
        ...
