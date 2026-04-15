from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.stok_hareketi import StokHareketi


class IStokHareketiRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 50,
        urun_id: Optional[int] = None,
        lot_id: Optional[int] = None,
        hareket_tipi: Optional[str] = None,
    ) -> List[StokHareketi]:
        ...

    @abstractmethod
    def olustur(self, hareket: StokHareketi, auto_commit: bool = True) -> StokHareketi:
        ...

    @abstractmethod
    def getir_son_hareket_palet_id_ile(self, palet_id: int) -> Optional[StokHareketi]:
        """
        Idempotency ve mükerrer işlem kontrolleri için,
        belirtilen palet ID'sine ait en son stok hareketini getirir.
        """
        ...

    @abstractmethod
    def siparis_icin_cikis_var_mi(self, siparis_no: str) -> bool:
        """Sipariş numarasına ait çıkış hareketi olup olmadığını kontrol eder."""
        ...

    @abstractmethod
    def siparis_icin_irsaliye_no_guncelle(
        self, siparis_no: str, irsaliye_no: str, auto_commit: bool = True
    ) -> int:
        """Sipariş çıkış hareketlerinden irsaliye_no=NULL olanları günceller.

        İrsaliye KESILDI/GONDERILDI geçişinde evrak numarasını stok hareketlerine
        geri yazmak için kullanılır. Daha önce irsaliye_no atanmış hareketler
        değiştirilmez (idempotency).

        Returns:
            Güncellenen satır sayısı.
        """
        ...


