from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.core.entities.stok_sayim import StokSayim, StokSayimKalemi


class IStokSayimRepository(ABC):

    @abstractmethod
    def getir_hepsi(self, skip: int = 0, limit: int = 100) -> List[StokSayim]:
        ...

    @abstractmethod
    def getir_id_ile(self, sayim_id: int) -> Optional[StokSayim]:
        """Kalemleriyle birlikte getirir."""
        ...

    @abstractmethod
    def olustur(self, sayim: StokSayim) -> StokSayim:
        ...

    @abstractmethod
    def guncelle(self, sayim: StokSayim) -> StokSayim:
        ...

    @abstractmethod
    def kalem_ekle(self, kalem: StokSayimKalemi) -> StokSayimKalemi:
        ...

    @abstractmethod
    def kalem_guncelle(self, kalem: StokSayimKalemi) -> StokSayimKalemi:
        ...

    @abstractmethod
    def kalem_getir_by_sayim_urun(self, sayim_id: int, urun_id: int) -> Optional[StokSayimKalemi]:
        """Sayım + ürün çiftine göre kalemi getirir (upsert desteği için)."""
        ...

    @abstractmethod
    def stok_snapshot_getir(self) -> Dict[int, int]:
        """Aktif ürünlerin palet bazlı stok toplamını döner: {urun_id: toplam_koli}."""
        ...
