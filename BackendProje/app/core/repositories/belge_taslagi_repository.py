"""Belge taslagi repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.core.entities.belge_taslagi import BelgeTaslagi


class IBelgeTaslagiRepository(ABC):
    @abstractmethod
    def getir_hepsi(
        self,
        skip: int = 0,
        limit: int = 100,
        durum: Optional[str] = None,
        depo_id: Optional[int] = None,
        max_confidence: Optional[float] = None,
    ) -> list[BelgeTaslagi]:
        ...

    @abstractmethod
    def getir_id_ile(self, taslak_id: int) -> Optional[BelgeTaslagi]:
        ...

    @abstractmethod
    def olustur(self, taslak: BelgeTaslagi, auto_commit: bool = False) -> BelgeTaslagi:
        ...

    @abstractmethod
    def guncelle(self, taslak: BelgeTaslagi, auto_commit: bool = False) -> BelgeTaslagi:
        ...
