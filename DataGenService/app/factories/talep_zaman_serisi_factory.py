"""Talep zaman serisi factory — ML eğitim verisi için (file emitter çıktısı).

Üretim modeli:
  - Her ürün için ``gun_sayisi`` günlük satış kaydı çıkarır.
  - Mevsimsellik (haftalık + yıllık) + trend + gürültü içerir.
  - Promosyon günleri rastgele (~%5 olasılık) miktarı 2-3x artırır.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Iterator
from datetime import date, timedelta
from typing import Any

from .base import BaseFactory, ReferenceTable
from .schemas import TalepGecmisKaydiDTO

REFERANS_BASLANGIC = date(2024, 1, 1)


class TalepZamanSerisiFactory(BaseFactory[TalepGecmisKaydiDTO]):
    """Talep geçmişi üretici. ``build_series`` çoklu kayıt için tercih edilir."""

    def __init__(
        self,
        seed: int = 42,
        locale: str = "tr_TR",
        urun_pool: ReferenceTable | None = None,
        baslangic: date = REFERANS_BASLANGIC,
    ) -> None:
        super().__init__(seed=seed, locale=locale)
        self.urun_pool = urun_pool or ReferenceTable()
        self.baslangic = baslangic

    def _build(self, index: int, **overrides: Any) -> TalepGecmisKaydiDTO:
        """Tek kayıt üretir; çoğu kullanım `build_series`'i tercih etmeli."""
        urun = (
            overrides.pop("urun", None)
            if "urun" in overrides
            else self.urun_pool.pick(self.rng)
        )
        gun = overrides.pop("tarih", self.baslangic + timedelta(days=index))

        # Mevsimsellik bileşeni.
        haftalik = 1.0 + 0.3 * math.sin(2 * math.pi * gun.weekday() / 7)
        yillik = 1.0 + 0.4 * math.sin(2 * math.pi * gun.timetuple().tm_yday / 365)
        baz = self.rng.randint(5, 50)
        gurultu = self.rng.gauss(1.0, 0.15)
        promosyon = self.rng.random() < 0.05
        carpan = self.rng.uniform(2.0, 3.0) if promosyon else 1.0

        miktar = max(0, int(baz * haftalik * yillik * gurultu * carpan))

        payload: dict[str, Any] = {
            "tarih": gun,
            "urun_kodu": urun["barkod"],
            "urun_id": urun["id"],
            "miktar": miktar,
            "fiyat": float(urun.get("fiyat", 0.0)),
            "promosyon": promosyon,
            "haftanin_gunu": gun.weekday(),
        }
        payload.update(overrides)
        return TalepGecmisKaydiDTO(**payload)

    def build_series(
        self,
        *,
        gun_sayisi: int,
        urun_subset: Iterable[dict[str, Any]] | None = None,
    ) -> Iterator[TalepGecmisKaydiDTO]:
        """Her ürün için ``gun_sayisi`` günlük tek bir streaming generator.

        Bellek dostu — büyük ürün kümeleri için parquet yazıcıya streamlenir.
        """
        if gun_sayisi < 1:
            raise ValueError("gun_sayisi >= 1 olmalı")

        self._reseed(self.seed)
        urunler = list(urun_subset) if urun_subset is not None else list(self.urun_pool)
        if not urunler:
            raise ValueError("Ürün havuzu boş — talep zaman serisi üretilemiyor.")

        for urun in urunler:
            for gun_idx in range(gun_sayisi):
                tarih = self.baslangic + timedelta(days=gun_idx)
                yield self._build(gun_idx, urun=urun, tarih=tarih)
