from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.palet_rezervasyonu import PaletRezervasyonu


class IPaletRezervasyonuRepository(ABC):

    @abstractmethod
    def olustur(self, rezervasyon: PaletRezervasyonu, auto_commit: bool = True) -> PaletRezervasyonu:
        ...

    @abstractmethod
    def guncelle(self, rezervasyon: PaletRezervasyonu, auto_commit: bool = True) -> Optional[PaletRezervasyonu]:
        ...

    @abstractmethod
    def getir_id_ile(self, rezervasyon_id: int) -> Optional[PaletRezervasyonu]:
        ...

    @abstractmethod
    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        siparis_id: Optional[int] = None,
    ) -> List[PaletRezervasyonu]:
        ...

    @abstractmethod
    def getir_siparis_rezervasyonlari(self, siparis_id: int) -> List[PaletRezervasyonu]:
        """Siparişe ait tüm rezervasyonları döner (tüm durumlar)."""
        ...

    @abstractmethod
    def getir_aktif_by_siparis(self, siparis_id: int) -> List[PaletRezervasyonu]:
        """Siparişe ait Aktif rezervasyonları döner."""
        ...

    @abstractmethod
    def getir_aktif_by_palet(self, palet_id: int) -> Optional[PaletRezervasyonu]:
        """Palete atanmış Aktif rezervasyonu döner; yoksa None.
        # TODO Faz 2: with_lock parametresi eklenecek (SELECT FOR UPDATE)
        """
        ...

    @abstractmethod
    def getir_by_sevkiyat_kalemi(self, sevkiyat_kalemi_id: int) -> Optional[PaletRezervasyonu]:
        ...

    @abstractmethod
    def rezerve_palet_idleri(self, urun_id: int) -> List[int]:
        """Belirtilen ürüne ait Aktif rezervasyonlardaki palet ID listesini döner."""
        ...
