"""Deterministik factory tabanı.

Determinism kuralı:
  - `__init__` Faker ve Random'u `seed` ile bir kez tohumlar.
  - `build_many` her çağrıda durumu seed'e sıfırlar; böylece aynı seed ile
    iki ayrı koşum byte-by-byte aynı listeyi üretir.
  - `build_one(index=k)` k'ıncı elemanı tekil olarak ister; underlying state'i
    ilerletmez (her çağrı kendi içinde reseed).

Referans bütünlüğü:
  - Bağımlı factory'ler (palet → lot → ürün → raf zinciri) `ReferenceTable`
    üzerinden parent kayıtların id/anahtarına erişir.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, TypeVar

from faker import Faker
from pydantic import BaseModel

DTO = TypeVar("DTO", bound=BaseModel)

DEFAULT_LOCALE = "tr_TR"


class ReferenceTable:
    """Üretim sırasında parent kayıtların kimliklerini tutan basit havuz.

    `id` int ya da str (lookup anahtarı) olabilir. Sıralama eklenme sırasına
    uyar; deterministik seçim için `pick(rng)` kullanılır.
    """

    __slots__ = ("_rows",)

    def __init__(self) -> None:
        self._rows: list[Mapping[str, Any]] = []

    def add(self, row: Mapping[str, Any]) -> None:
        self._rows.append(dict(row))

    def extend(self, rows: list[Mapping[str, Any]]) -> None:
        for row in rows:
            self.add(row)

    def __len__(self) -> int:
        return len(self._rows)

    def __iter__(self):
        return iter(self._rows)

    def pick(self, rng: random.Random) -> Mapping[str, Any]:
        if not self._rows:
            raise ValueError(
                "ReferenceTable boş — bağımlı factory çağrılmadan önce parent "
                "kayıtların eklenmesi gerekir."
            )
        return self._rows[rng.randrange(len(self._rows))]

    def at(self, index: int) -> Mapping[str, Any]:
        if not self._rows:
            raise ValueError("ReferenceTable boş.")
        return self._rows[index % len(self._rows)]


class BaseFactory(ABC, Generic[DTO]):
    """Pydantic DTO üreten deterministik factory tabanı.

    Alt sınıflar `_build(index, **overrides) -> DTO` metodunu implement eder.
    `Faker` ve `random.Random` instance'ları her factory'ye özel; global state
    kullanılmaz. Bu, paralel testlerde çakışmayı önler.
    """

    def __init__(
        self,
        seed: int = 42,
        locale: str = DEFAULT_LOCALE,
    ) -> None:
        self.seed = seed
        self.locale = locale
        self.faker: Faker = Faker(locale)
        self.rng: random.Random = random.Random()
        self._reseed(seed)

    def _reseed(self, seed: int) -> None:
        """Underlying Faker + Random state'lerini deterministik biçimde sıfırlar."""
        self.faker.seed_instance(seed)
        self.rng.seed(seed)

    @abstractmethod
    def _build(self, index: int, **overrides: Any) -> DTO:
        """index'inci elemanı üret. Faker/rng yalnız buradan tüketilmelidir."""

    def build_one(self, index: int = 0, **overrides: Any) -> DTO:
        """index'inci elemanı tek seferlik üretir.

        Çağrı izolasyonu için state index'e kadar ilerletilir; böylece
        `build_one(5)` çağrısı her zaman aynı sonucu döner.
        """
        self._reseed(self.seed)
        # State'i k'ıncı elemana taşımak için 0..index-1 atılır.
        for i in range(index):
            self._build(i, **overrides)
        return self._build(index, **overrides)

    def build_many(self, count: int, **overrides: Any) -> list[DTO]:
        """count adet eleman üretir; her çağrıda state seed'e sıfırlanır."""
        if count < 0:
            raise ValueError(f"count negatif olamaz: {count}")
        self._reseed(self.seed)
        return [self._build(i, **overrides) for i in range(count)]
