"""Servisler arası kimlik — INTERNAL_API_KEY header doğrulaması.

Sibling servislerin (AgvSimService, vb.) güvenli callback yapabilmesi için
JWT'den ayrı, paylaşımlı bir secret kullanılır. Anahtar ayarlanmamışsa
istek reddedilir (production-safe).
"""

from __future__ import annotations

import logging

from fastapi import Header, HTTPException, status

from app.core.config import get_settings

log = logging.getLogger(__name__)


def internal_api_key_verify(
    x_internal_api_key: str | None = Header(default=None, alias="X-Internal-Api-Key"),
) -> None:
    settings = get_settings()
    expected = settings.internal_api_key
    if not expected:
        log.warning(
            "INTERNAL_API_KEY ayarlanmamis — internal callback endpoint'leri devre disi"
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Internal API kimligi yapilandirilmamis",
        )
    if x_internal_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Internal API kimligi gecersiz",
        )
