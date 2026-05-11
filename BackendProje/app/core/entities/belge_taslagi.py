"""DocAi belge taslagi domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


class BelgeTaslagiDurum:
    KABUL_BEKLIYOR = "KABUL_BEKLIYOR"
    KABUL_EDILDI = "KABUL_EDILDI"
    REDDEDILDI = "REDDEDILDI"

    _GECISLER = {
        KABUL_BEKLIYOR: {KABUL_EDILDI, REDDEDILDI},
        KABUL_EDILDI: set(),
        REDDEDILDI: set(),
    }

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


@dataclass
class BelgeTaslagi:
    id: Optional[int] = None
    kaynak_dosya_yolu: Optional[str] = None
    belge_tipi: str = "IRSALIYE"
    ham_json: dict[str, Any] = field(default_factory=dict)
    durum: str = BelgeTaslagiDurum.KABUL_BEKLIYOR
    confidence_skoru: float = 0.0
    olusturan_kullanici_id: Optional[int] = None
    depo_id: int = 0
    mal_kabul_irsaliye_id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def kabul_edildi(self, mal_kabul_irsaliye_id: int) -> None:
        if not BelgeTaslagiDurum.gecis_gecerli_mi(
            self.durum,
            BelgeTaslagiDurum.KABUL_EDILDI,
        ):
            raise ValueError(f"Belge taslagi durum gecisi gecersiz: {self.durum}")
        self.durum = BelgeTaslagiDurum.KABUL_EDILDI
        self.mal_kabul_irsaliye_id = mal_kabul_irsaliye_id
        self.updated_at = datetime.utcnow()

    def reddet(self) -> None:
        if not BelgeTaslagiDurum.gecis_gecerli_mi(
            self.durum,
            BelgeTaslagiDurum.REDDEDILDI,
        ):
            raise ValueError(f"Belge taslagi durum gecisi gecersiz: {self.durum}")
        self.durum = BelgeTaslagiDurum.REDDEDILDI
        self.updated_at = datetime.utcnow()
