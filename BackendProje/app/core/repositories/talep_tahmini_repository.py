from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class TalepTahminUrunKaydi:
    id: int
    isim: str
    barkod: Optional[str]
    min_stok: int
    stok_miktari: int


@dataclass(frozen=True)
class GunlukCikisKaydi:
    tarih: date
    miktar: float


class ITalepTahminiRepository(ABC):
    @abstractmethod
    def urunleri_listele(
        self,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> list[TalepTahminUrunKaydi]:
        ...

    @abstractmethod
    def urun_getir(self, urun_id: int) -> Optional[TalepTahminUrunKaydi]:
        ...

    @abstractmethod
    def gunluk_cikislari_getir(
        self,
        urun_id: int,
        baslangic: date,
        bitis: date,
    ) -> list[GunlukCikisKaydi]:
        ...

