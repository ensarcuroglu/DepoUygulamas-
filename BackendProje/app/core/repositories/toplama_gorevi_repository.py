from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.toplama_gorevi import ToplamaGorevi


class IToplamaGoreviRepository(ABC):

    @abstractmethod
    def olustur(self, gorev: ToplamaGorevi, auto_commit: bool = True) -> ToplamaGorevi:
        ...

    @abstractmethod
    def guncelle(self, gorev: ToplamaGorevi, auto_commit: bool = True) -> Optional[ToplamaGorevi]:
        ...

    @abstractmethod
    def getir_id_ile(self, gorev_id: int) -> Optional[ToplamaGorevi]:
        ...

    @abstractmethod
    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        depo_id: Optional[int] = None,
        kullanici_id: Optional[int] = None,
        sevkiyat_id: Optional[int] = None,
    ) -> List[ToplamaGorevi]:
        ...

    @abstractmethod
    def getir_next_bekleyen(
        self,
        depo_id: Optional[int] = None,
        with_lock: bool = False,
    ) -> Optional[ToplamaGorevi]:
        """Pull-based: sıra_no ASC, olusturma_tarihi ASC ilk Beklemede görevi döner.
        with_lock=True → SELECT FOR UPDATE SKIP LOCKED (eşzamanlı operatör güvenliği).
        """
        ...

    @abstractmethod
    def getir_sevkiyat_gorevleri(self, sevkiyat_id: int) -> List[ToplamaGorevi]:
        ...

    @abstractmethod
    def gorev_var_mi(self, sevkiyat_id: int, palet_id: int) -> bool:
        """Belirtilen sevkiyat+palet için aktif görev var mı? (idempotency guard)"""
        ...
