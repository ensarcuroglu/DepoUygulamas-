from abc import ABC, abstractmethod

from app.core.entities.palet_durum_log import PaletDurumLog


class IPaletDurumLogRepository(ABC):

    @abstractmethod
    def olustur(self, log: PaletDurumLog, auto_commit: bool = False) -> PaletDurumLog:
        ...
