"""Toplama görev factory — sevkiyat id üzerinden tetiklenir."""

from __future__ import annotations

from typing import Any

from .base import BaseFactory, ReferenceTable
from .schemas import ToplamaGoreviDTO


class ToplamaGorevFactory(BaseFactory[ToplamaGoreviDTO]):
    """`ToplamaGoreviDTO` üretici (POST /api/v1/toplama-gorevleri/uret).

    Backend `sevkiyat_id` üzerinden N toplama görevi üretir; bu factory
    yalnız tetikleyici payload üretir.
    """

    def __init__(
        self,
        seed: int = 42,
        locale: str = "tr_TR",
        sevkiyat_pool: ReferenceTable | None = None,
    ) -> None:
        super().__init__(seed=seed, locale=locale)
        self.sevkiyat_pool = sevkiyat_pool or ReferenceTable()

    def _build(self, index: int, **overrides: Any) -> ToplamaGoreviDTO:
        if "sevkiyat_id" in overrides:
            sevkiyat_id = overrides.pop("sevkiyat_id")
        elif len(self.sevkiyat_pool) > 0:
            sevkiyat_id = self.sevkiyat_pool.pick(self.rng)["id"]
        else:
            # Pool yoksa deterministik artan id üret.
            sevkiyat_id = index + 1

        payload: dict[str, Any] = {"sevkiyat_id": sevkiyat_id}
        payload.update(overrides)
        return ToplamaGoreviDTO(**payload)
