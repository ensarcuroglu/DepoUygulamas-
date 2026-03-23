from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.kategori import Kategori


class IKategoriRepository(ABC):

    @abstractmethod
    def getir_hepsi(self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True) -> List[Kategori]:
        ...

    @abstractmethod
    def getir_id_ile(self, kategori_id: int) -> Optional[Kategori]:
        ...

    @abstractmethod
    def olustur(self, kategori: Kategori) -> Kategori:
        ...

    @abstractmethod
    def guncelle(self, kategori: Kategori) -> Kategori:
        ...

    @abstractmethod
    def getir_isim_ile(self, isim: str) -> Optional[Kategori]:
        """İsme göre kategori arar (case-insensitive)."""
        ...

    @abstractmethod
    def sil(self, kategori_id: int) -> bool:
        ...
