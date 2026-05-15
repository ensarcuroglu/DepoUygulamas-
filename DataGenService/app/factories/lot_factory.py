"""Lot factory — ürüne bağlı."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .base import BaseFactory, ReferenceTable
from .schemas import LotDTO


class LotFactory(BaseFactory[LotDTO]):
    """`LotDTO` üretici. `urun_pool` ile aktif ürünlerden seçer.

    ``urun_pool`` boşsa explicit ``urun_id`` override edilmedikçe hata verir.
    """

    def __init__(
        self,
        seed: int = 42,
        locale: str = "tr_TR",
        urun_pool: ReferenceTable | None = None,
    ) -> None:
        super().__init__(seed=seed, locale=locale)
        self.urun_pool = urun_pool or ReferenceTable()

    def _build(self, index: int, **overrides: Any) -> LotDTO:
        if "urun_id" in overrides:
            urun_id = overrides.pop("urun_id")
        else:
            urun_id = self.urun_pool.pick(self.rng)["id"]

        # Üretim tarihi son 365 gün; SKT 30-720 gün sonrası.
        bugun = date(2026, 5, 15)
        uretim = bugun - timedelta(days=self.rng.randint(0, 365))
        skt = uretim + timedelta(days=self.rng.randint(30, 720))

        lot_no = overrides.pop(
            "lot_no",
            f"LOT-{uretim:%Y%m%d}-{index:05d}",
        )
        parti_no = overrides.pop("parti_no", f"P{self.rng.randint(10000, 99999)}")

        payload: dict[str, Any] = {
            "urun_id": urun_id,
            "lot_no": lot_no,
            "parti_no": parti_no,
            "uretim_tarihi": uretim,
            "son_kullanma_tarihi": skt,
            "aciklama": "",
        }
        payload.update(overrides)
        return LotDTO(**payload)
