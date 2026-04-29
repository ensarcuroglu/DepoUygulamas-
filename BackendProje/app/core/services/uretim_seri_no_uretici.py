from abc import ABC, abstractmethod
from datetime import date


class IUretimSeriNoUretici(ABC):
    """Port: prefix bazlı palet seri numarası üretici."""

    @abstractmethod
    def uret(self, tarih: date, prefix: str = "PRD") -> str:
        """Verilen tarih ve prefix için benzersiz seri no üretir.

        Format: {PREFIX}-YYYYMMDD-NNNN
        Desteklenen prefix'ler: PRD (üretim), MKB (mal kabul)
        Transaction rollback'te gap kabul edilir.
        """
        ...
