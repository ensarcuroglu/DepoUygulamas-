from abc import ABC, abstractmethod
from datetime import date


class IUretimSeriNoUretici(ABC):
    """Port: üretim paleti seri numarası üretici."""

    @abstractmethod
    def uret(self, tarih: date) -> str:
        """Verilen tarih için benzersiz seri no üretir.

        Format: PRD-YYYYMMDD-NNNN
        Transaction rollback'te gap kabul edilir.
        """
        ...
