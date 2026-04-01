from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.urun import Urun


class IUrunRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        search: Optional[str] = None,
        kategori_id: Optional[int] = None,
        marka_id: Optional[int] = None,
        sadece_aktif: bool = True,
    ) -> List[Urun]:
        ...

    @abstractmethod
    def getir_id_ile(self, urun_id: int) -> Optional[Urun]:
        ...

    @abstractmethod
    def getir_barkod_ile(self, barkod: str) -> Optional[Urun]:
        ...

    @abstractmethod
    def getir_ean_ile(self, ean: str) -> Optional[Urun]:
        ...

    @abstractmethod
    def olustur(self, urun: Urun) -> Urun:
        ...

    @abstractmethod
    def guncelle(self, urun: Urun) -> Urun:
        ...

    @abstractmethod
    def sil(self, urun_id: int) -> bool:
        ...

    @abstractmethod
    def getir_kritik_stoklar(self) -> List[Urun]:
        """min_stok eşiğinin altındaki ürünleri döner."""
        ...
