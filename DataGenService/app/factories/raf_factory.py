"""Raf factory — referans havuz parçası."""

from __future__ import annotations

from typing import Any

from .base import BaseFactory
from .schemas import RafDTO

_KORIDORLAR = ("A", "B", "C", "D", "E", "F")


class RafFactory(BaseFactory[RafDTO]):
    """`RafDTO` üretici. Depo kapsamında raf grid'i üretir.

    Kod formatı: ``{depo_kodu}-{koridor}-{kat:02d}-{goz:02d}``
    Örn: ``DPO1-A-03-12``.
    """

    def _build(self, index: int, **overrides: Any) -> RafDTO:
        depo_id = overrides.pop("depo_id", self.rng.randint(1, 3))
        depo_kodu = overrides.pop("depo_kodu", f"DPO{depo_id}")
        zon_id = overrides.pop("zon_id", self.rng.randint(1, 5))

        koridor = self.rng.choice(_KORIDORLAR)
        kat = self.rng.randint(0, 4)
        goz = self.rng.randint(1, 30)
        kod = f"{depo_kodu}-{koridor}-{kat:02d}-{goz:02d}"

        kapasite = self.rng.choice((50, 80, 100, 150, 200))
        max_agirlik = round(self.rng.uniform(500.0, 2000.0), 1)

        payload: dict[str, Any] = {
            "depo_id": depo_id,
            "zon_id": zon_id,
            "kod": kod,
            "bolge": "",
            "kapasite": kapasite,
            "max_agirlik_kg": max_agirlik,
            "koridor": koridor,
            "kat": kat,
            "goz": goz,
        }
        payload.update(overrides)
        return RafDTO(**payload)
