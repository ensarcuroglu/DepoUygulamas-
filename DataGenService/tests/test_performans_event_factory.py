"""Faz 5 — PerformansEventFactory testleri."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

import pytest

from app.factories import PerformansEventDTO, PerformansEventFactory


@pytest.mark.unit
def test_deterministic_output() -> None:
    a = PerformansEventFactory(seed=42).build_many(50)
    b = PerformansEventFactory(seed=42).build_many(50)
    assert [e.model_dump() for e in a] == [e.model_dump() for e in b]


@pytest.mark.unit
def test_output_validates_against_dto() -> None:
    factory = PerformansEventFactory(seed=42)
    for e in factory.build_many(100):
        assert isinstance(e, PerformansEventDTO)
        assert e.event_tipi in {"GOREV_BASLATILDI", "GOREV_TAMAMLANDI", "GOREV_IPTAL"}
        assert e.gorev_tipi in {"yerlestirme", "toplama"}
        assert 1 <= e.kullanici_id <= 50
        assert 1 <= e.depo_id <= 3  # default depo_count
        if e.event_tipi == "GOREV_TAMAMLANDI":
            assert e.sure_saniye is not None and e.sure_saniye >= 15
            assert e.iptal_nedeni is None
        elif e.event_tipi == "GOREV_IPTAL":
            assert e.iptal_nedeni is not None
            assert e.sure_saniye is None


@pytest.mark.unit
def test_event_uuid_unique_per_index() -> None:
    events = PerformansEventFactory(seed=42).build_many(500)
    uuidler = [e.event_uuid for e in events]
    assert len(set(uuidler)) == 500, "event_uuid collision (rastgele 128-bit beklenir)"


@pytest.mark.unit
def test_event_tipi_dagilim_yaklasik_dogru() -> None:
    """%30 BASLATILDI / %55 TAMAMLANDI / %15 IPTAL — büyük örneklemde tutarlı."""
    events = PerformansEventFactory(seed=42).build_many(5_000)
    sayim = Counter(e.event_tipi for e in events)
    # 5K örneklemde her bin ±%5 toleransta olmalı
    assert 0.25 * 5_000 < sayim["GOREV_BASLATILDI"] < 0.35 * 5_000
    assert 0.50 * 5_000 < sayim["GOREV_TAMAMLANDI"] < 0.60 * 5_000
    assert 0.10 * 5_000 < sayim["GOREV_IPTAL"] < 0.20 * 5_000


@pytest.mark.unit
def test_invalid_constructor_args() -> None:
    with pytest.raises(ValueError, match="kullanici_count"):
        PerformansEventFactory(seed=1, kullanici_count=0)
    with pytest.raises(ValueError, match="depo_count"):
        PerformansEventFactory(seed=1, depo_count=0)


@pytest.mark.unit
def test_override_event_tipi() -> None:
    factory = PerformansEventFactory(seed=42)
    e = factory.build_one(0, event_tipi="GOREV_TAMAMLANDI")
    assert e.event_tipi == "GOREV_TAMAMLANDI"
    assert e.sure_saniye is not None


@pytest.mark.unit
def test_baz_zaman_offset() -> None:
    baz = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    factory = PerformansEventFactory(seed=42, baz_zaman=baz)
    events = factory.build_many(100)
    for e in events:
        delta = abs((e.olusturma_tarihi - baz).total_seconds())
        assert delta <= 5 * 3600
