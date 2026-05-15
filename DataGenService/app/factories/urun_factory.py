"""Ürün factory — referans havuz başlangıcı."""

from __future__ import annotations

import random
from typing import Any

from .base import BaseFactory
from .schemas import Birim, DepolamaTipi, UrunDTO

_BIRIMLER: tuple[Birim, ...] = ("Adet", "Kg", "Lt", "Mt")
_DEPOLAMA_TIPLERI: tuple[DepolamaTipi, ...] = ("Kuru", "Soguk", "Tehlikeli")
_KATEGORI_PREFIX = ("GIDA", "TKM", "ICK", "MET", "PLS", "KIM")


def _ean13(rng: random.Random) -> str:
    """EAN-13 üretici (12 hane rastgele + 1 checksum)."""
    base = "".join(str(rng.randint(0, 9)) for _ in range(12))
    total = sum(
        int(d) * (3 if i % 2 else 1)
        for i, d in enumerate(base)
    )
    checksum = (10 - total % 10) % 10
    return f"{base}{checksum}"


class UrunFactory(BaseFactory[UrunDTO]):
    """`UrunDTO` üretici. Referans havuzun başlangıç noktası."""

    def _build(self, index: int, **overrides: Any) -> UrunDTO:
        prefix = self.rng.choice(_KATEGORI_PREFIX)
        # SKU: deterministik artan + prefix; barkod harici çakışma riskini azaltır.
        barkod = f"{prefix}-{index:06d}"

        # Ağırlık kategorisine bağlı koli adetleri.
        ic_adet = self.rng.choice((6, 12, 24, 48))
        gramaj = round(self.rng.uniform(0.05, 5.0), 3)
        fiyat = round(self.rng.uniform(2.5, 250.0), 2)

        payload: dict[str, Any] = {
            "isim": f"{self.faker.word().capitalize()} {self.faker.color_name()} {ic_adet}'li",
            "marka_id": self.rng.randint(1, 30),
            "kategori_id": self.rng.randint(1, 15),
            "tedarikci_id": self.rng.randint(1, 50),
            "ean": _ean13(self.rng),
            "barkod": barkod,
            "ic_adet": ic_adet,
            "gramaj": gramaj,
            "birim": self.rng.choice(_BIRIMLER),
            "fiyat": fiyat,
            "min_stok": self.rng.choice((5, 10, 20, 50)),
            "aciklama": "",
            "depolama_tipi": self.rng.choice(_DEPOLAMA_TIPLERI),
        }
        payload.update(overrides)
        return UrunDTO(**payload)
