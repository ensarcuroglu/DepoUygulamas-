"""Servisler arası kimlik — INTERNAL_API_KEY header doğrulaması."""

from __future__ import annotations

import logging

from fastapi import Header, HTTPException, status

from config import settings

log = logging.getLogger(__name__)


def internal_api_key_verify(
    x_internal_api_key: str | None = Header(default=None, alias="X-Internal-Api-Key"),
) -> None:
    """Header `X-Internal-Api-Key` settings.INTERNAL_API_KEY ile eşleşmeli.

    Anahtar ayarlanmamışsa (boş) — geliştirme/test ortamı için açık bırakılır,
    ancak uyarı log'lanır.
    """
    if not settings.INTERNAL_API_KEY:
        log.warning("INTERNAL_API_KEY ayarlanmamis — auth devre disi (yalnizca dev ortami)")
        return
    if x_internal_api_key != settings.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Internal API key gecersiz",
        )
