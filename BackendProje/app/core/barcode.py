"""Barcode sanitization and format validation helpers."""

from __future__ import annotations

import re
from typing import Optional


CONTROL_CHARS_RE = re.compile(r"[\x00-\x1F\x7F]")
ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200F\uFEFF]")
PALET_BARKOD_PATTERN = re.compile(
    r"^(PRD-\d{8}-\d{1,5}|MKB-\d{8}-\d{1,5}|PLT-[\w-]{1,30}|\d{4,10})$",
    re.IGNORECASE,
)
# Raf kodu serbest formdadır (depo bazında farklı şemalar).
# Asıl semantik doğrulama raf_repo.getir_kod_ile ile DB'de yapılır.
# Burada sadece kaba format/güvenlik filtresi: harf+rakam+tire, 2-40 karakter,
# en az bir alfanümerik içermeli, tire ile başlayıp/bitmemeli.
RAF_BARKOD_PATTERN = re.compile(r"^(?=.*[A-Z0-9])[A-Z0-9](?:[A-Z0-9-]{0,38}[A-Z0-9])?$", re.IGNORECASE)


def sanitize_barkod(value: Optional[str]) -> str:
    if value is None:
        return ""
    sanitized = CONTROL_CHARS_RE.sub("", str(value))
    sanitized = ZERO_WIDTH_RE.sub("", sanitized)
    sanitized = re.sub(r"\s+", "", sanitized)
    return sanitized.strip().upper()


def validate_palet_barkod(value: str) -> str:
    sanitized = sanitize_barkod(value)
    if not PALET_BARKOD_PATTERN.fullmatch(sanitized):
        raise ValueError(
            "Palet barkod formati hatali. "
            "Ornekler: PRD-20260424-001, MKB-20260429-001, PLT-TEDARIK-001"
        )
    return sanitized


def validate_raf_barkod(value: str) -> str:
    sanitized = sanitize_barkod(value)
    if not RAF_BARKOD_PATTERN.fullmatch(sanitized):
        raise ValueError(
            "Raf barkod formati hatali. Sadece harf, rakam ve tire kullanin "
            "(2-40 karakter). Ornek: A-01, GNL-A-01-01-01"
        )
    return sanitized
