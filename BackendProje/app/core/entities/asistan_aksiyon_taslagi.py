"""Asistan aksiyon taslagi domain entity.

AssistantAiService LLM'i HITL (Human-in-the-Loop) bir tool calistirmak istediginde,
gercek DB mutasyonu yerine onerilen aksiyon bu tabloya yazilir. Kullanici frontend'de
"Onayla" bastiginda authoritative use case tetiklenir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


class AsistanTaslakDurum:
    BEKLEMEDE = "BEKLEMEDE"
    ONAYLANDI = "ONAYLANDI"
    REDDEDILDI = "REDDEDILDI"
    SURESI_DOLDU = "SURESI_DOLDU"

    _GECISLER = {
        BEKLEMEDE: {ONAYLANDI, REDDEDILDI, SURESI_DOLDU},
        ONAYLANDI: set(),
        REDDEDILDI: set(),
        SURESI_DOLDU: set(),
    }

    @classmethod
    def gecis_gecerli_mi(cls, mevcut: str, hedef: str) -> bool:
        return hedef in cls._GECISLER.get(mevcut, set())


@dataclass
class AsistanAksiyonTaslagi:
    id: Optional[int] = None
    kullanici_id: int = 0
    rol: str = ""
    tool_id: str = ""
    payload_json: dict[str, Any] = field(default_factory=dict)
    durum: str = AsistanTaslakDurum.BEKLEMEDE
    ozet: Optional[str] = None
    idempotency_key: str = ""
    sonuc_json: Optional[dict[str, Any]] = None
    hata_mesaji: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None

    def suresi_dolmus_mu(self, simdi: Optional[datetime] = None) -> bool:
        simdi = simdi or datetime.utcnow()
        return self.expires_at <= simdi

    def onayla(self, sonuc: Optional[dict[str, Any]] = None) -> None:
        if not AsistanTaslakDurum.gecis_gecerli_mi(
            self.durum, AsistanTaslakDurum.ONAYLANDI
        ):
            raise ValueError(f"Asistan taslagi durum gecisi gecersiz: {self.durum}")
        self.durum = AsistanTaslakDurum.ONAYLANDI
        self.sonuc_json = sonuc
        self.executed_at = datetime.utcnow()

    def reddet(self) -> None:
        if not AsistanTaslakDurum.gecis_gecerli_mi(
            self.durum, AsistanTaslakDurum.REDDEDILDI
        ):
            raise ValueError(f"Asistan taslagi durum gecisi gecersiz: {self.durum}")
        self.durum = AsistanTaslakDurum.REDDEDILDI
        self.executed_at = datetime.utcnow()

    def suresi_doldu(self) -> None:
        if not AsistanTaslakDurum.gecis_gecerli_mi(
            self.durum, AsistanTaslakDurum.SURESI_DOLDU
        ):
            raise ValueError(f"Asistan taslagi durum gecisi gecersiz: {self.durum}")
        self.durum = AsistanTaslakDurum.SURESI_DOLDU
        self.executed_at = datetime.utcnow()
