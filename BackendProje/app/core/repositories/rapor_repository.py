from abc import ABC, abstractmethod
from typing import List, Optional

from app.core.entities.rapor import RaporSablonu, RaporLogu, RaporSchedule


class IRaporSablonuRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        tur: Optional[str] = None, is_aktif: bool = True,
    ) -> List[RaporSablonu]:
        ...

    @abstractmethod
    def getir_id_ile(self, sablon_id: int) -> Optional[RaporSablonu]:
        ...

    @abstractmethod
    def olustur(self, sablon: RaporSablonu) -> RaporSablonu:
        ...

    @abstractmethod
    def guncelle(self, sablon: RaporSablonu) -> RaporSablonu:
        ...

    @abstractmethod
    def sil(self, sablon_id: int) -> bool:
        ...


class IRaporLoguRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        sablon_id: Optional[int] = None,
    ) -> List[RaporLogu]:
        ...

    @abstractmethod
    def olustur(self, log: RaporLogu) -> RaporLogu:
        ...


class IRaporScheduleRepository(ABC):

    @abstractmethod
    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        is_aktif: bool = True,
    ) -> List[RaporSchedule]:
        ...

    @abstractmethod
    def getir_id_ile(self, schedule_id: int) -> Optional[RaporSchedule]:
        ...

    @abstractmethod
    def olustur(self, schedule: RaporSchedule) -> RaporSchedule:
        ...

    @abstractmethod
    def guncelle(self, schedule: RaporSchedule) -> RaporSchedule:
        ...

    @abstractmethod
    def sil(self, schedule_id: int) -> bool:
        ...
