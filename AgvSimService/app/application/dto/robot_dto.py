"""Robot snapshot DTO'ları."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class RobotDTO(BaseModel):
    id: str
    x: int
    y: int
    durum: str
    yon: str
    gorev_id: Optional[str] = None
    rota_kalan: int = 0


class RobotSnapshotResponseDTO(BaseModel):
    tick_no: int
    robotlar: list[RobotDTO]
