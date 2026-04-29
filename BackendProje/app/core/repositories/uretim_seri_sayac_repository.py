from abc import ABC, abstractmethod
from datetime import date


class IUretimSeriSayacRepository(ABC):

    @abstractmethod
    def artir_ve_dondur(self, tarih: date, prefix: str = "PRD") -> int:
        """SELECT FOR UPDATE ile sayacı atomik olarak artırır ve yeni değeri döner.

        prefix: Kaynak bazlı prefix (PRD=üretim, MKB=mal kabul).
        Transaction rollback'te gap kabul edilir (sequence gap is by design).
        """
        ...
