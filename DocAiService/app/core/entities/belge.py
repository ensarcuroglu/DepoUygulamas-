"""Document extraction domain entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.core.entities.irsaliye_taslagi import IrsaliyeTaslagiSchema


class BelgeTipi(str, Enum):
    TEXT_PDF = "TEXT_PDF"
    SCANNED_PDF = "SCANNED_PDF"
    IMAGE = "IMAGE"


@dataclass(frozen=True)
class Belge:
    filename: str
    content_type: str | None
    content: bytes

    @property
    def size_bytes(self) -> int:
        return len(self.content)


@dataclass(frozen=True)
class BelgeAlani:
    path: str
    value: Any
    confidence: float


@dataclass(frozen=True)
class ExtractionSonucu:
    belge_tipi: BelgeTipi
    taslak: IrsaliyeTaslagiSchema
    raw_text: str
    model: str
    metadata: dict[str, Any] = field(default_factory=dict)
