from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.etiket_sablonu import EtiketSablonu


class IEtiketSablonuRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100, sadece_aktif: bool = True
    ) -> List[EtiketSablonu]:
        ...

    @abstractmethod
    def getir_id_ile(self, sablon_id: int) -> Optional[EtiketSablonu]:
        ...

    @abstractmethod
    def getir_default(self) -> Optional[EtiketSablonu]:
        ...

    @abstractmethod
    def olustur(self, sablon: EtiketSablonu) -> EtiketSablonu:
        ...

    @abstractmethod
    def guncelle(self, sablon: EtiketSablonu) -> Optional[EtiketSablonu]:
        ...

    @abstractmethod
    def sil(self, sablon_id: int) -> bool:
        ...

    @abstractmethod
    def default_sifirla(self, haric_id: Optional[int] = None) -> None:
        """Tüm şablonların default_mi'sini False yapar; haric_id verilirse o dışarıda kalır."""
        ...
