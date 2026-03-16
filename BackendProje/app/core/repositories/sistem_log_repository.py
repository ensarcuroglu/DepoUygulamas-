from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.sistem_log import SistemLog


class ISistemLogRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        modul: Optional[str] = None,
        islem_tipi: Optional[str] = None,
    ) -> List[SistemLog]:
        ...

    @abstractmethod
    def olustur(self, log: SistemLog, auto_commit: bool = True) -> SistemLog:
        ...
