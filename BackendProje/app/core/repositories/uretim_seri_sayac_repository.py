from abc import ABC, abstractmethod
from datetime import date


class IUretimSeriSayacRepository(ABC):

    @abstractmethod
    def artir_ve_dondur(self, tarih: date) -> int:
        """SELECT FOR UPDATE ile sayacı atomik olarak artırır ve yeni değeri döner.

        Transaction rollback'te gap kabul edilir (sequence gap is by design).
        """
        ...
