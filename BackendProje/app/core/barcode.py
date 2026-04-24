"""Barcode sanitization and format validation helpers."""

from __future__ import annotations

import re
from typing import Optional


CONTROL_CHARS_RE = re.compile(r"[\x00-\x1F\x7F]")
ZERO_WIDTH_RE = re.compile(r"[\u200B-\u200F\uFEFF]")
PALET_BARKOD_PATTERN = re.compile(r"^PRD-\d{8}-\d{1,5}$", re.IGNORECASE)
RAF_BARKOD_PATTERN = re.compile(r"^[A-Z]{2,4}-[A-Z]-\d{2}-\d{2}-\d{2}$", re.IGNORECASE)


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
        raise ValueError("Barkod formati hatali. Ornek: PRD-20260424-001")
    return sanitized


def validate_raf_barkod(value: str) -> str:
    sanitized = sanitize_barkod(value)
    if not RAF_BARKOD_PATTERN.fullmatch(sanitized):
        raise ValueError("Raf barkod formati hatali. Ornek: GNL-A-01-01-01")
    return sanitized
