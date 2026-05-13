"""Unit testleri — RabbitMQ event serializer.

Round-trip ve schema_version doğrulaması.
"""

from __future__ import annotations

import json
from datetime import datetime

import pytest

from app.core.entities.operator_performans import (
    GorevPerformansEvent,
    PerformansEventTipi,
    PerformansGorevTipi,
)
from app.infrastructure.messaging.serializer import (
    PERFORMANS_EVENT_SCHEMA_VERSION,
    deserialize_performans_event,
    serialize_performans_event,
)


pytestmark = pytest.mark.unit


def _ornek_event() -> GorevPerformansEvent:
    return GorevPerformansEvent(
        id=42,
        event_uuid="11111111-2222-3333-4444-555555555555",
        event_tipi=PerformansEventTipi.GOREV_TAMAMLANDI,
        gorev_tipi=PerformansGorevTipi.YERLESTIRME,
        gorev_id=999,
        kullanici_id=7,
        depo_id=1,
        sure_saniye=320,
        iptal_nedeni=None,
        payload={"raf": "A-01-02"},
        olusturma_tarihi=datetime(2026, 5, 13, 10, 0, 0),
    )


class TestSerializer:
    def test_payload_schema_version_iceri(self):
        body = serialize_performans_event(_ornek_event())
        parsed = json.loads(body)
        assert parsed["schema_version"] == PERFORMANS_EVENT_SCHEMA_VERSION

    def test_round_trip_korur(self):
        ornek = _ornek_event()
        body = serialize_performans_event(ornek)
        gelen = deserialize_performans_event(body)

        assert gelen.id == ornek.id
        assert gelen.event_uuid == ornek.event_uuid
        assert gelen.event_tipi == ornek.event_tipi
        assert gelen.gorev_tipi == ornek.gorev_tipi
        assert gelen.gorev_id == ornek.gorev_id
        assert gelen.kullanici_id == ornek.kullanici_id
        assert gelen.depo_id == ornek.depo_id
        assert gelen.sure_saniye == ornek.sure_saniye
        assert gelen.iptal_nedeni == ornek.iptal_nedeni
        assert gelen.payload == ornek.payload
        assert gelen.olusturma_tarihi == ornek.olusturma_tarihi

    def test_iptal_eventi_iptal_nedeni_korur(self):
        ornek = GorevPerformansEvent(
            id=1,
            event_uuid="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
            event_tipi=PerformansEventTipi.GOREV_IPTAL,
            gorev_tipi=PerformansGorevTipi.TOPLAMA,
            gorev_id=2,
            kullanici_id=3,
            iptal_nedeni="kullanici_birakti",
            olusturma_tarihi=datetime(2026, 5, 13, 11, 30, 0),
        )
        gelen = deserialize_performans_event(serialize_performans_event(ornek))
        assert gelen.iptal_nedeni == "kullanici_birakti"
        assert gelen.event_tipi == PerformansEventTipi.GOREV_IPTAL

    def test_desteklenmeyen_schema_hata_firlatir(self):
        body = json.dumps({"schema_version": 99, "event_tipi": "x"}).encode("utf-8")
        with pytest.raises(ValueError, match="schema_version"):
            deserialize_performans_event(body)

    def test_unicode_payload_korunur(self):
        ornek = _ornek_event()
        ornek.payload = {"aciklama": "Türkçe karakter ÖŞŞĞÜ", "sayı": 5}
        gelen = deserialize_performans_event(serialize_performans_event(ornek))
        assert gelen.payload == ornek.payload
