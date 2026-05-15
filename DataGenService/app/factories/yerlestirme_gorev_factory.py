"""Yerleştirme görev factory — palet + raf'a bağlı."""

from __future__ import annotations

from typing import Any

from .base import BaseFactory, ReferenceTable
from .schemas import YerlestirmeGoreviDTO


class YerlestirmeGorevFactory(BaseFactory[YerlestirmeGoreviDTO]):
    """`YerlestirmeGoreviDTO` üretici (POST /api/yerlestirme-gorevleri/)."""

    def __init__(
        self,
        seed: int = 42,
        locale: str = "tr_TR",
        palet_pool: ReferenceTable | None = None,
        raf_pool: ReferenceTable | None = None,
    ) -> None:
        super().__init__(seed=seed, locale=locale)
        self.palet_pool = palet_pool or ReferenceTable()
        self.raf_pool = raf_pool or ReferenceTable()

    def _build(self, index: int, **overrides: Any) -> YerlestirmeGoreviDTO:
        palet_id = (
            overrides.pop("palet_id", None) or self.palet_pool.pick(self.rng)["id"]
        )
        onerilen_raf_id = (
            overrides.pop("onerilen_raf_id", None)
            or self.raf_pool.pick(self.rng)["id"]
        )

        payload: dict[str, Any] = {
            "palet_id": palet_id,
            "mal_kabul_irsaliye_id": None,
            "tip": "yerlestirme",
            "kaynak_raf_id": None,
            "onerilen_raf_id": onerilen_raf_id,
            "oncelik": self.rng.randint(1, 5),
        }
        payload.update(overrides)
        return YerlestirmeGoreviDTO(**payload)
