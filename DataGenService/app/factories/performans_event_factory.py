"""Performans event factory — RabbitMQ `task_load --target=rabbit` için.

Backend'in `GorevPerformansEvent` yapısıyla uyumlu deterministik üretici.
Üretilen event'ler `lms.gorev_performans.<event_tipi>` routing key'i ile
yayılır. Consumer DB'de karşılık bulamayacağı için DLQ'ya düşmesi
beklenir — bu **yük testi** akışıdır (envanter §2).

Event tipi dağılımı: ~%30 BASLATILDI, %55 TAMAMLANDI, %15 IPTAL — saha
profiline yakın oranlar.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from .base import BaseFactory
from .schemas import GorevTipi, PerformansEventDTO, PerformansEventTipi


_EVENT_DAGILIMI: tuple[tuple[PerformansEventTipi, int], ...] = (
    ("GOREV_BASLATILDI", 30),
    ("GOREV_TAMAMLANDI", 55),
    ("GOREV_IPTAL", 15),
)
_GOREV_TIPLERI: tuple[GorevTipi, ...] = ("yerlestirme", "toplama")
_IPTAL_NEDENLERI = (
    "Palet bulunamadi",
    "Hatali raf",
    "Operator iptal",
    "Sistemsel hata",
)


class PerformansEventFactory(BaseFactory[PerformansEventDTO]):
    """`PerformansEventDTO` üretici.

    Args:
        kullanici_count: Sahte operatör kümesi (id 1..N rastgele seçilir).
        depo_count: Sahte depo kümesi.
        baz_zaman: ``olusturma_tarihi`` referansı; her event ±5 saatlik bir
                   offset alır.
    """

    def __init__(
        self,
        seed: int = 42,
        locale: str = "tr_TR",
        *,
        kullanici_count: int = 50,
        depo_count: int = 3,
        baz_zaman: datetime | None = None,
    ) -> None:
        super().__init__(seed=seed, locale=locale)
        if kullanici_count < 1:
            raise ValueError("kullanici_count >= 1 olmalı")
        if depo_count < 1:
            raise ValueError("depo_count >= 1 olmalı")
        self.kullanici_count = kullanici_count
        self.depo_count = depo_count
        self.baz_zaman = baz_zaman or datetime(2026, 5, 15, 8, 0, tzinfo=timezone.utc)

    def _build(self, index: int, **overrides: Any) -> PerformansEventDTO:
        event_tipi = overrides.pop(
            "event_tipi", self._weighted_event_tipi()
        )
        gorev_tipi = overrides.pop("gorev_tipi", self.rng.choice(_GOREV_TIPLERI))

        # Deterministik UUID — seed + index'ten türetilir.
        event_uuid = overrides.pop(
            "event_uuid",
            str(uuid.UUID(int=self.rng.getrandbits(128))),
        )

        # ±5 saat offset
        offset_sn = self.rng.randint(-5 * 3600, 5 * 3600)
        olusturma = self.baz_zaman + timedelta(seconds=offset_sn)

        sure_saniye: int | None = None
        iptal_nedeni: str | None = None
        if event_tipi == "GOREV_TAMAMLANDI":
            sure_saniye = self.rng.randint(15, 600)
        elif event_tipi == "GOREV_IPTAL":
            iptal_nedeni = self.rng.choice(_IPTAL_NEDENLERI)

        payload: dict[str, Any] = {
            "event_uuid": event_uuid,
            "event_tipi": event_tipi,
            "gorev_tipi": gorev_tipi,
            "gorev_id": overrides.pop(
                "gorev_id", self.rng.randint(1, 1_000_000)
            ),
            "kullanici_id": overrides.pop(
                "kullanici_id", self.rng.randint(1, self.kullanici_count)
            ),
            "depo_id": overrides.pop(
                "depo_id", self.rng.randint(1, self.depo_count)
            ),
            "sure_saniye": sure_saniye,
            "iptal_nedeni": iptal_nedeni,
            "payload": None,
            "olusturma_tarihi": olusturma,
        }
        payload.update(overrides)
        return PerformansEventDTO(**payload)

    def _weighted_event_tipi(self) -> PerformansEventTipi:
        toplam = sum(w for _, w in _EVENT_DAGILIMI)
        r = self.rng.randint(1, toplam)
        kumulatif = 0
        for tip, agirlik in _EVENT_DAGILIMI:
            kumulatif += agirlik
            if r <= kumulatif:
                return tip
        return _EVENT_DAGILIMI[-1][0]  # fallback
