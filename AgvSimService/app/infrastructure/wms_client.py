"""HTTP WMS callback port — async httpx client."""

from __future__ import annotations

import logging

import httpx

from app.core.services.wms_callback_port import IWmsCallbackPort, WmsCallbackPayload

log = logging.getLogger(__name__)


class HttpWmsCallbackPort(IWmsCallbackPort):
    def __init__(
        self,
        wms_base_url: str,
        api_key: str | None,
        timeout: float = 5.0,
    ) -> None:
        self._url = wms_base_url.rstrip("/") + "/api/agv-callbacks/gorev-tamamlandi"
        self._api_key = api_key
        self._timeout = timeout

    async def gorev_tamamlandi(self, payload: WmsCallbackPayload) -> bool:
        if not self._api_key:
            log.warning("WMS callback atlandi: INTERNAL_API_KEY yok")
            return False

        body = {
            "wms_gorev_id": payload.wms_gorev_id,
            "wms_gorev_tipi": payload.wms_gorev_tipi,
            "robot_id": payload.robot_id,
            "gerceklesen_raf_id": payload.gerceklesen_raf_id,
            "sim_baslama_tick": payload.sim_baslama_tick,
            "sim_tamamlanma_tick": payload.sim_tamamlanma_tick,
            "rota_uzunlugu": payload.rota_uzunlugu,
        }
        headers = {"X-Internal-Api-Key": self._api_key}

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(self._url, json=body, headers=headers)
        except httpx.RequestError as exc:
            log.warning("WMS callback baglanti hatasi gorev=%s: %s", payload.wms_gorev_id, exc)
            return False

        if response.status_code == 200:
            log.info(
                "WMS callback ok gorev=%s status=%s",
                payload.wms_gorev_id,
                response.json().get("status"),
            )
            return True

        log.warning(
            "WMS callback reddedildi gorev=%s status=%s body=%s",
            payload.wms_gorev_id,
            response.status_code,
            response.text[:200],
        )
        return False
