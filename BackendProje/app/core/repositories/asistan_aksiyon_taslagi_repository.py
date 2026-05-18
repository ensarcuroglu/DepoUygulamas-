"""Asistan aksiyon taslagi repository port."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.core.entities.asistan_aksiyon_taslagi import AsistanAksiyonTaslagi


class IAsistanAksiyonTaslagiRepository(ABC):
    @abstractmethod
    def getir_id_ile(
        self, taslak_id: int, kilitli_mi: bool = False
    ) -> Optional[AsistanAksiyonTaslagi]:
        ...

    @abstractmethod
    def getir_idempotency_ile(
        self, idempotency_key: str
    ) -> Optional[AsistanAksiyonTaslagi]:
        ...

    @abstractmethod
    def getir_hepsi(
        self,
        kullanici_id: Optional[int] = None,
        durum: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[AsistanAksiyonTaslagi]:
        ...

    @abstractmethod
    def olustur(
        self, taslak: AsistanAksiyonTaslagi, auto_commit: bool = False
    ) -> AsistanAksiyonTaslagi:
        ...

    @abstractmethod
    def guncelle(
        self, taslak: AsistanAksiyonTaslagi, auto_commit: bool = False
    ) -> AsistanAksiyonTaslagi:
        ...
