"""GorevPerformansEvent ↔ JSON serileştirme.

Mesaj şeması (schema_version=1):

    {
      "schema_version": 1,
      "event_id": 123,
      "event_uuid": "uuid-string",
      "event_tipi": "GOREV_TAMAMLANDI",
      "gorev_tipi": "yerlestirme",
      "gorev_id": 456,
      "kullanici_id": 7,
      "depo_id": 1,
      "sure_saniye": 320,
      "iptal_nedeni": null,
      "payload": {},
      "olusturma_tarihi": "2026-05-12T10:00:00Z"
    }

Consumer mesajı tüketirken `event_uuid` veya `event_id` üzerinden DB'de
idempotent lookup yapar.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

from app.core.entities.operator_performans import GorevPerformansEvent


PERFORMANS_EVENT_SCHEMA_VERSION = 1


def _iso_utc(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    # naive datetime'ı UTC kabul ederiz (publisher/aggregator zaten utcnow kullanıyor).
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _from_iso_utc(value: str | None) -> datetime | None:
    if value is None:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt


def serialize_performans_event(event: GorevPerformansEvent) -> bytes:
    """Event'i UTF-8 JSON byte dizisine çevirir."""
    body: Dict[str, Any] = {
        "schema_version": PERFORMANS_EVENT_SCHEMA_VERSION,
        "event_id": event.id,
        "event_uuid": event.event_uuid,
        "event_tipi": event.event_tipi,
        "gorev_tipi": event.gorev_tipi,
        "gorev_id": event.gorev_id,
        "kullanici_id": event.kullanici_id,
        "depo_id": event.depo_id,
        "sure_saniye": event.sure_saniye,
        "iptal_nedeni": event.iptal_nedeni,
        "payload": event.payload,
        "olusturma_tarihi": _iso_utc(event.olusturma_tarihi),
    }
    return json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def deserialize_performans_event(raw: bytes | str) -> GorevPerformansEvent:
    """JSON mesajı entity'ye çevirir. Schema versiyonu desteklenmiyorsa hata."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    data = json.loads(raw)

    schema_version = data.get("schema_version")
    if schema_version != PERFORMANS_EVENT_SCHEMA_VERSION:
        raise ValueError(
            f"Desteklenmeyen schema_version: {schema_version!r} "
            f"(beklenen: {PERFORMANS_EVENT_SCHEMA_VERSION})"
        )

    return GorevPerformansEvent(
        id=data.get("event_id"),
        event_uuid=data.get("event_uuid"),
        event_tipi=data["event_tipi"],
        gorev_tipi=data["gorev_tipi"],
        gorev_id=data["gorev_id"],
        kullanici_id=data["kullanici_id"],
        depo_id=data.get("depo_id"),
        sure_saniye=data.get("sure_saniye"),
        iptal_nedeni=data.get("iptal_nedeni"),
        payload=data.get("payload"),
        olusturma_tarihi=_from_iso_utc(data.get("olusturma_tarihi")) or datetime.utcnow(),
    )
