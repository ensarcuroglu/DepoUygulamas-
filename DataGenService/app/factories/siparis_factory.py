"""Sipariş factory — kalemler ürün havuzundan seçilir."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .base import BaseFactory, ReferenceTable
from .schemas import SiparisDTO, SiparisKalemDTO


class SiparisFactory(BaseFactory[SiparisDTO]):
    """`SiparisDTO` üretici. Her sipariş 1-N kalem içerir."""

    def __init__(
        self,
        seed: int = 42,
        locale: str = "tr_TR",
        urun_pool: ReferenceTable | None = None,
        min_kalem: int = 1,
        max_kalem: int = 5,
    ) -> None:
        super().__init__(seed=seed, locale=locale)
        self.urun_pool = urun_pool or ReferenceTable()
        self.min_kalem = min_kalem
        self.max_kalem = max_kalem

    def _build(self, index: int, **overrides: Any) -> SiparisDTO:
        bugun = date(2026, 5, 15)
        teslimat = overrides.pop(
            "teslimat_tarihi",
            bugun + timedelta(days=self.rng.randint(1, 30)),
        )

        kalem_sayisi = self.rng.randint(self.min_kalem, self.max_kalem)
        kalemler: list[SiparisKalemDTO] = []
        # Aynı ürünün iki kez seçilmesini önlemek için seçim havuzunu daralt.
        secilen_urun_idleri: set[int] = set()
        for _ in range(kalem_sayisi):
            for _try in range(10):
                urun = self.urun_pool.pick(self.rng)
                if urun["id"] not in secilen_urun_idleri:
                    break
            secilen_urun_idleri.add(urun["id"])
            kalemler.append(
                SiparisKalemDTO(
                    urun_id=urun["id"],
                    miktar=self.rng.randint(1, 50),
                    birim_fiyat=round(self.rng.uniform(5.0, 200.0), 2),
                    kdv_orani=self.rng.choice((1.0, 8.0, 18.0, 20.0)),
                )
            )

        payload: dict[str, Any] = {
            "musteri_adi": overrides.pop("musteri_adi", self.faker.company()),
            "teslimat_adresi": overrides.pop(
                "teslimat_adresi",
                self.faker.address().replace("\n", ", "),
            ),
            "teslimat_tarihi": teslimat,
            "notlar": "",
            "kalemler": kalemler,
        }
        payload.update(overrides)
        return SiparisDTO(**payload)
