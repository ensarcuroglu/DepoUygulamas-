"""WebSocket telemetri payload tipleri (referans/dokümantasyon).

WS gönderimi `dict` üzerinden yapılır; bu DTO'lar serialize doğrulaması için
opsiyoneldir. (FastAPI WS handler şu an `send_text` ile JSON gönderir.)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class WsSnapshotMesaji(BaseModel):
    tip: Literal["snapshot"] = "snapshot"
    tick_no: int
    ts: float
    grid: dict[str, Any]
    robotlar: list[dict[str, Any]]


class WsDeltaMesaji(BaseModel):
    tip: Literal["delta"] = "delta"
    tick_no: int
    ts: float
    robotlar: list[dict[str, Any]]
    kuyruk_uzunlugu: int = 0
    aktif_gorev_sayisi: int = 0


class WsEventMesaji(BaseModel):
    tip: Literal["event"] = "event"
    olay: str
    robot_id: str | None = None
    gorev_id: str | None = None
    rota: list[list[int]] | None = None
