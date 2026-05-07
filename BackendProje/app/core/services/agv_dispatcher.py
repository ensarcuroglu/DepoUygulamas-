"""AGV dispatcher port + dataclass payload + NoOp default.

Tasarım:
- `IAgvDispatcher` core katmanında soyutlanmış arayüz (port).
- HTTP implementasyonu `app/infrastructure/services/http_agv_dispatcher.py`'da.
- Default: `NoOpAgvDispatcher` — feature flag kapalı veya AGV servisi
  yoksa kullanılır; böylece use case'ler iç değişiklik gerektirmez.

Davranış sözleşmesi:
- Dispatch çağrıları **fire-and-forget** mantığıyla çalışır.
- Hiçbir hata yukarıya bubble edilmez (use case transaction'ı bozulmamalı).
- Uygunluk kontrolü (feature flag) implementasyonun sorumluluğundadır.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AgvDispatchPayload:
    """AGV servisine gönderilecek görev payload'ı."""

    wms_gorev_id: int
    wms_gorev_tipi: str          # "Yerlestirme" | "Toplama" | "Transfer" | "BelirsizKonum"
    depo_id: int
    kaynak_raf_id: int           # Geçilebilir hedef için "yaklaşma" rafının id'si
    hedef_raf_id: int
    palet_id: Optional[int] = None
    oncelik: int = 5             # 1=Acil … 5=Normal


class IAgvDispatcher(ABC):
    """AGV servisine görev yönlendirme port'u."""

    @abstractmethod
    def dispatch_yerlestirme(self, payload: AgvDispatchPayload) -> None:
        """Yerleştirme görevini AGV'ye gönder.

        - Feature flag kapalı/depo dışındaysa: no-op.
        - Hata olsa dahi raise etmez (görev WMS'te BEKLIYOR'da kalır,
          insan operatör manuel alabilir).
        """


class NoOpAgvDispatcher(IAgvDispatcher):
    """Feature kapalıyken kullanılan default implementasyon."""

    def dispatch_yerlestirme(self, payload: AgvDispatchPayload) -> None:  # noqa: D401
        return None
