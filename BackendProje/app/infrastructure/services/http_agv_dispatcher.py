"""HTTP implementasyonu — AGV servisine httpx ile POST atar."""

from __future__ import annotations

import logging
from typing import Iterable

import httpx

from app.core.services.agv_dispatcher import AgvDispatchPayload, IAgvDispatcher

log = logging.getLogger(__name__)


class HttpAgvDispatcher(IAgvDispatcher):
    """Görev oluşturma sonrası AGV servisine fire-and-forget HTTP POST.

    Kasıtlı tasarım kararları:
    - **Sync httpx.Client** — use case sync; FastAPI route handler thread-pool'da
      çalışıyor; bu yüzden burada async gerekmiyor.
    - **Kısa timeout (default 2s)** — AGV ulaşılamazsa görev WMS'te BEKLIYOR'da
      kalır ve insan operatör doğal akışında devralır.
    - **Hatalar yukarıya bubble edilmez** — sadece warning log'lanır. Use case
      transaction bütünlüğü korunur.
    - **Idempotency anahtarı yok** — AGV iç gorev_id üretiyor; aynı WMS görev
      ID'si farklı agv_gorev_id'lerle iki kez push edilse bile WMS callback
      idempotent olacak (router seviyesinde).
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None,
        pilot_depo_ids: Iterable[int],
        timeout: float = 2.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._pilot_depo_ids = set(pilot_depo_ids)
        self._timeout = timeout

    def _eligible(self, depo_id: int | None) -> bool:
        if not self._pilot_depo_ids:
            return False
        if -1 in self._pilot_depo_ids:
            return True
        if depo_id is None:
            return False
        return depo_id in self._pilot_depo_ids

    def dispatch_yerlestirme(self, payload: AgvDispatchPayload) -> None:
        if not self._eligible(payload.depo_id):
            return
        if not self._api_key:
            log.warning(
                "AGV dispatch atlandi: INTERNAL_API_KEY ayarlanmamis (gorev=%s)",
                payload.wms_gorev_id,
            )
            return

        url = f"{self._base_url}/api/agv/gorevler"
        body = {
            "wms_gorev_id": payload.wms_gorev_id,
            "wms_gorev_tipi": payload.wms_gorev_tipi,
            "depo_id": payload.depo_id,
            "kaynak_raf_id": payload.kaynak_raf_id,
            "hedef_raf_id": payload.hedef_raf_id,
            "palet_id": payload.palet_id,
            "oncelik": payload.oncelik,
        }
        headers = {"X-Internal-Api-Key": self._api_key}

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=body, headers=headers)
        except httpx.RequestError as exc:
            log.warning(
                "AGV dispatch baglanti hatasi gorev=%s: %s",
                payload.wms_gorev_id,
                exc,
            )
            return

        if response.status_code != 200:
            log.warning(
                "AGV dispatch reddedildi gorev=%s status=%s body=%s",
                payload.wms_gorev_id,
                response.status_code,
                response.text[:200],
            )
            return

        try:
            agv_id = response.json().get("agv_gorev_id")
        except ValueError:
            agv_id = None
        log.info(
            "AGV dispatch ok gorev=%s agv_gorev_id=%s",
            payload.wms_gorev_id,
            agv_id,
        )
