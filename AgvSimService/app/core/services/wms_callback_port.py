"""WMS callback port — AGV görev tamamlandığında WMS'e bildirim arayüzü.

Tasarım:
- Port (interface) core katmanında. HTTP implementasyonu infrastructure'da.
- NoOp default — testler ve WMS olmadan çalışan dev için.
- Async: callback IO-bound (httpx async client).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class WmsCallbackPayload:
    """WMS'e gönderilecek tamamlanma callback payload'ı."""

    wms_gorev_id: int
    wms_gorev_tipi: str
    robot_id: str
    gerceklesen_raf_id: int
    sim_baslama_tick: Optional[int] = None
    sim_tamamlanma_tick: Optional[int] = None
    rota_uzunlugu: Optional[int] = None


class IWmsCallbackPort(ABC):
    @abstractmethod
    async def gorev_tamamlandi(self, payload: WmsCallbackPayload) -> bool:
        """True → WMS başarılı kapadı; False → hata, AGV görev orphan kalır."""


class NoOpWmsCallbackPort(IWmsCallbackPort):
    """WMS yokken (dev/test) kullanılır. Her zaman başarılı."""

    async def gorev_tamamlandi(self, payload: WmsCallbackPayload) -> bool:
        return True
