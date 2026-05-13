"""Unit testleri — MetriklerAggregasyonUseCase.eventleri_isle.

Faz 4 refactor sonrası çekirdek metod hem DB polling (execute()) hem
consumer worker (per-message) tarafından kullanılır. Bu testler:
  * tek event aggregasyonu (consumer akışı)
  * çoklu event batch (polling akışı)
  * tüketim hesabı tutarlılığı (yerlestirme/toplama/iptal sayaçları)
  * boş liste no-op
  * execute() bekleyen event'leri okur ve eventleri_isle delege eder
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional

import pytest

from app.application.use_cases.operator_performans_use_cases import (
    MetriklerAggregasyonUseCase,
)
from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    PerformansEventTipi,
    PerformansGorevTipi,
)
from app.core.services.operator_kpi_service import OperatorKpiService


pytestmark = pytest.mark.unit


# ─────────────────────── fakes ───────────────────────


@dataclass
class _FakeEventRepo:
    bekleyenler: list = field(default_factory=list)
    aggregate_isaretlenenler: list = field(default_factory=list)

    def bekleyen_eventleri_getir(self, limit: int = 500):
        return list(self.bekleyenler[:limit])

    def aggregate_edildi_isaretle(
        self, event_idleri, auto_commit: bool = True
    ) -> int:
        self.aggregate_isaretlenenler.extend(event_idleri)
        return len(event_idleri)

    # Faz 2 metodları — bu testlerde kullanılmıyor ama ABC ile uyum.
    def olustur(self, event, auto_commit: bool = False):
        return event

    def yayinlanmamis_eventleri_getir(self, limit: int = 100):
        return []

    def yayinlandi_isaretle(self, event_id, yayin_tarihi=None, auto_commit=True):
        return True

    def yayin_hatasi_kaydet(self, event_id, hata, auto_commit=True):
        return True


@dataclass
class _FakeMetrikRepo:
    cagrilar: list = field(default_factory=list)

    def upsert_artir(
        self,
        kullanici_id: int,
        vardiya_tarihi: date,
        depo_id: Optional[int],
        yerlestirme_delta: int = 0,
        toplama_delta: int = 0,
        iptal_delta: int = 0,
        sure_saniye_delta: int = 0,
        auto_commit: bool = True,
    ):
        self.cagrilar.append(
            {
                "kullanici_id": kullanici_id,
                "vardiya_tarihi": vardiya_tarihi,
                "depo_id": depo_id,
                "yerlestirme": yerlestirme_delta,
                "toplama": toplama_delta,
                "iptal": iptal_delta,
                "sure_saniye": sure_saniye_delta,
            }
        )
        return None

    # Diğer ABC metodları — testlerde dokunulmuyor.
    def getir_kullanici_tarih_ile(self, *args, **kwargs):
        return None

    def getir_aralik(self, *args, **kwargs):
        return []

    def leaderboard_getir(self, *args, **kwargs):
        return []


def _event(
    *,
    id: int,
    event_tipi: str = PerformansEventTipi.GOREV_TAMAMLANDI,
    gorev_tipi: str = PerformansGorevTipi.YERLESTIRME,
    kullanici_id: int = 7,
    sure_saniye: Optional[int] = 300,
    tarih: datetime = datetime(2026, 5, 13, 10, 0, 0),
) -> GorevPerformansEvent:
    return GorevPerformansEvent(
        id=id,
        event_uuid=f"uuid-{id}",
        event_tipi=event_tipi,
        gorev_tipi=gorev_tipi,
        gorev_id=1000 + id,
        kullanici_id=kullanici_id,
        depo_id=1,
        sure_saniye=sure_saniye,
        olusturma_tarihi=tarih,
    )


def _build_uc(
    bekleyenler: list[GorevPerformansEvent] | None = None,
) -> tuple[MetriklerAggregasyonUseCase, _FakeEventRepo, _FakeMetrikRepo]:
    event_repo = _FakeEventRepo(bekleyenler=bekleyenler or [])
    metrik_repo = _FakeMetrikRepo()
    uc = MetriklerAggregasyonUseCase(
        event_repo=event_repo,
        metrik_repo=metrik_repo,
        kpi_service=OperatorKpiService(),
    )
    return uc, event_repo, metrik_repo


# ─────────────────────── tests ───────────────────────


class TestEventleriIsle:
    def test_bos_liste_no_op(self):
        uc, e, m = _build_uc()
        sonuc = uc.eventleri_isle([])
        assert sonuc.islenen_event == 0
        assert sonuc.guncellenen_vardiya == 0
        assert m.cagrilar == []
        assert e.aggregate_isaretlenenler == []

    def test_tek_event_yerlestirme_tamamlandi(self):
        uc, e, m = _build_uc()
        sonuc = uc.eventleri_isle([_event(id=1)])
        assert sonuc.islenen_event == 1
        assert sonuc.guncellenen_vardiya == 1
        assert e.aggregate_isaretlenenler == [1]
        assert len(m.cagrilar) == 1
        assert m.cagrilar[0]["yerlestirme"] == 1
        assert m.cagrilar[0]["sure_saniye"] == 300

    def test_iki_event_ayni_vardiya_tek_upsert(self):
        eventler = [
            _event(id=1, gorev_tipi=PerformansGorevTipi.YERLESTIRME),
            _event(
                id=2,
                gorev_tipi=PerformansGorevTipi.TOPLAMA,
                sure_saniye=180,
            ),
        ]
        uc, e, m = _build_uc()
        sonuc = uc.eventleri_isle(eventler)
        assert sonuc.islenen_event == 2
        assert sonuc.guncellenen_vardiya == 1
        assert len(m.cagrilar) == 1
        assert m.cagrilar[0]["yerlestirme"] == 1
        assert m.cagrilar[0]["toplama"] == 1
        assert m.cagrilar[0]["sure_saniye"] == 480

    def test_iptal_eventi_iptal_sayaca_yansir(self):
        uc, e, m = _build_uc()
        uc.eventleri_isle([
            _event(
                id=3,
                event_tipi=PerformansEventTipi.GOREV_IPTAL,
                sure_saniye=60,
            )
        ])
        assert m.cagrilar[0]["iptal"] == 1
        assert m.cagrilar[0]["sure_saniye"] == 60

    def test_iki_farkli_kullanici_iki_upsert(self):
        eventler = [
            _event(id=1, kullanici_id=7),
            _event(id=2, kullanici_id=9),
        ]
        uc, e, m = _build_uc()
        sonuc = uc.eventleri_isle(eventler)
        assert sonuc.guncellenen_vardiya == 2
        assert len(m.cagrilar) == 2

    def test_consumer_call_pattern_tek_event_iki_kez_idempotent_degil_di(self):
        """eventleri_isle idempotency garanti etmez; consumer DB seviyesinde
        aggregate_edildi=True kontrolü yapmalıdır. Bu test çekirdek metodun
        her çağrıda sayaçları artırdığını doğrular (idempotency üst katmanda)."""
        uc, e, m = _build_uc()
        uc.eventleri_isle([_event(id=1)])
        uc.eventleri_isle([_event(id=1)])  # aynı id — yine sayar
        assert len(m.cagrilar) == 2
        assert e.aggregate_isaretlenenler == [1, 1]


class TestExecute:
    def test_execute_bekleyenleri_okur_ve_delege_eder(self):
        eventler = [_event(id=i) for i in range(1, 4)]
        uc, e, m = _build_uc(bekleyenler=eventler)
        sonuc = uc.execute()
        assert sonuc.islenen_event == 3
        assert e.aggregate_isaretlenenler == [1, 2, 3]

    def test_execute_bos_outbox_no_op(self):
        uc, e, m = _build_uc(bekleyenler=[])
        sonuc = uc.execute()
        assert sonuc.islenen_event == 0
        assert m.cagrilar == []
