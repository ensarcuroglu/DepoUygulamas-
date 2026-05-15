"""Palet factory — lot + raf'a bağlı."""

from __future__ import annotations

from typing import Any

from .base import BaseFactory, ReferenceTable
from .schemas import PaletDTO

_VARDIYALAR = ("Sabah", "Oglen", "Aksam", "Gece")


class PaletFactory(BaseFactory[PaletDTO]):
    """`PaletDTO` üretici. `lot_pool` ve `raf_pool` referansları zorunlu."""

    def __init__(
        self,
        seed: int = 42,
        locale: str = "tr_TR",
        lot_pool: ReferenceTable | None = None,
        raf_pool: ReferenceTable | None = None,
    ) -> None:
        super().__init__(seed=seed, locale=locale)
        self.lot_pool = lot_pool or ReferenceTable()
        self.raf_pool = raf_pool or ReferenceTable()

    def _build(self, index: int, **overrides: Any) -> PaletDTO:
        lot_id = overrides.pop("lot_id", None) or self.lot_pool.pick(self.rng)["id"]
        raf_id = overrides.pop("raf_id", None) or self.raf_pool.pick(self.rng)["id"]

        palet_no = overrides.pop("palet_no", f"PLT-{index:07d}")
        koli_adedi = overrides.pop("koli_adedi", self.rng.randint(10, 80))
        palet_kg = overrides.pop("palet_kg", round(self.rng.uniform(50.0, 950.0), 2))
        vardiya = overrides.pop("vardiya", self.rng.choice(_VARDIYALAR))

        payload: dict[str, Any] = {
            "lot_id": lot_id,
            "raf_id": raf_id,
            "palet_no": palet_no,
            "koli_adedi": koli_adedi,
            "palet_kg": palet_kg,
            "vardiya": vardiya,
        }
        payload.update(overrides)
        return PaletDTO(**payload)
