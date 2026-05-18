"""Langfuse Cloud tracing wrapper with safe no-op fallback.

Sibling AI servisleriyle ayni davranis: `LANGFUSE_TRACING_ENABLED` aciksa
gercek client kullanilir, kapaliysa veya kurulu degilse butun cagrilar no-op
olur. Boylece test/local geliştirme Langfuse'siz calisir.
"""

from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)


def _enabled() -> bool:
    raw = os.environ.get("LANGFUSE_TRACING_ENABLED", "false")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


try:
    from langfuse import Langfuse  # type: ignore

    _AVAILABLE = True
except ImportError:  # pragma: no cover - optional dep
    _AVAILABLE = False
    Langfuse = None  # type: ignore


_client: Any | None = None


def _get_client() -> Any | None:
    """Lazy-initialize a Langfuse client. Returns None when disabled."""
    global _client
    if not _enabled() or not _AVAILABLE:
        return None
    if _client is None:
        try:
            _client = Langfuse(
                public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
                secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
                host=os.environ.get("LANGFUSE_BASE_URL"),
            )
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("Langfuse init failed; tracing disabled: %s", exc)
            _client = None
    return _client


def flush() -> None:
    """Best-effort flush; safe to call even when tracing is disabled."""
    client = _get_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:  # pragma: no cover - defensive
        log.warning("Langfuse flush failed: %s", exc)
