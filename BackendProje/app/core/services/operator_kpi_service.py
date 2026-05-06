"""Operatör KPI Domain Service.

Saf domain mantığı: event listesinden vardiya bazlı delta'lar üretir.
Repository'den bağımsız — kolay unit test edilebilir.

UPH ve hata oranı, OperatorVardiyaMetrikleri entity üzerindeki property'ler
ile okuma sırasında hesaplanır; bu serviste saklanmaz.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, List, Tuple

from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    PerformansEventTipi,
    PerformansGorevTipi,
)


@dataclass(frozen=True)
class VardiyaAnahtari:
    """Aggregasyon anahtarı: (kullanici_id, vardiya_tarihi)."""

    kullanici_id: int
    vardiya_tarihi: date


@dataclass
class VardiyaDelta:
    """Bir vardiya kovasına uygulanacak delta'lar."""

    yerlestirme_delta: int = 0
    toplama_delta: int = 0
    iptal_delta: int = 0
    sure_saniye_delta: int = 0
    depo_id: int | None = None
    isleneN_event_idleri: List[int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.isleneN_event_idleri is None:
            self.isleneN_event_idleri = []


class OperatorKpiService:
    """Event listesini vardiya kovalarına grupluyor.

    Karar:
      - Vardiya = takvim günü (UTC). Event.olusturma_tarihi.date() bucket key.
      - GOREV_BASLATILDI ham olay olarak kaydedilir ama metriklerde sayılmaz
        (yalnızca işaretleme amaçlı). KPI'lar TAMAMLANDI ve IPTAL üzerinden
        türetilir.
      - Hata = İptal (kararlaştırıldı). v2'de daha kompleks tanım.
    """

    def vardiya_delta_uret(
        self, eventler: Iterable[GorevPerformansEvent]
    ) -> List[Tuple[VardiyaAnahtari, VardiyaDelta]]:
        """Event'leri (kullanici, gün) bazında grupluyor delta listesi üretir.

        Dönen liste deterministik sırayla — önce vardiya_tarihi, sonra
        kullanici_id artan.
        """
        kovalar: dict[VardiyaAnahtari, VardiyaDelta] = {}

        for event in eventler:
            if event.id is None:
                continue
            if event.kullanici_id <= 0:
                continue

            anahtar = VardiyaAnahtari(
                kullanici_id=event.kullanici_id,
                vardiya_tarihi=event.olusturma_tarihi.date(),
            )
            kova = kovalar.get(anahtar)
            if kova is None:
                kova = VardiyaDelta(depo_id=event.depo_id)
                kovalar[anahtar] = kova
            elif kova.depo_id is None and event.depo_id is not None:
                kova.depo_id = event.depo_id

            kova.isleneN_event_idleri.append(event.id)

            if event.event_tipi == PerformansEventTipi.GOREV_TAMAMLANDI:
                if event.gorev_tipi == PerformansGorevTipi.YERLESTIRME:
                    kova.yerlestirme_delta += 1
                elif event.gorev_tipi == PerformansGorevTipi.TOPLAMA:
                    kova.toplama_delta += 1
                if event.sure_saniye and event.sure_saniye > 0:
                    kova.sure_saniye_delta += event.sure_saniye
            elif event.event_tipi == PerformansEventTipi.GOREV_IPTAL:
                kova.iptal_delta += 1
                if event.sure_saniye and event.sure_saniye > 0:
                    kova.sure_saniye_delta += event.sure_saniye
            # GOREV_BASLATILDI: yalnızca işaretle — sayaca yansımaz.

        return sorted(
            kovalar.items(),
            key=lambda kv: (kv[0].vardiya_tarihi, kv[0].kullanici_id),
        )
