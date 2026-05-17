"""Langfuse Cloud tracing helpers for ExcelAiService.

The helpers are intentionally no-op unless tracing is explicitly enabled and
Langfuse credentials are present. This keeps observability from becoming part
of the request success path.
"""

from __future__ import annotations

import logging
import os
import re
from contextlib import ExitStack, contextmanager, nullcontext
from typing import Any, Iterator

logger = logging.getLogger(__name__)

SERVICE_NAME = "excel-ai"
DEFAULT_LANGFUSE_BASE_URL = "https://cloud.langfuse.com"
_TRUTHY = {"1", "true", "yes", "on"}
_MAX_STRING_CHARS = 2000
_SUMMARY_PREVIEW_CHARS = 160

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
_LONG_NUMBER_RE = re.compile(r"(?<!\d)\d{10,}(?!\d)")
_BASE64_RE = re.compile(r"^[A-Za-z0-9+/=\s]{400,}$")
_SENSITIVE_KEYS = {
    "content",
    "document",
    "file",
    "file_name",
    "file_path",
    "filename",
    "filepath",
    "image",
    "image_base64",
    "images",
    "messages",
    "output",
    "path",
    "prompt",
    "prompts",
    "raw",
    "raw_output",
}
_PAYLOAD_KEYS = {"answer", "cevap", "input", "question", "soru", *_SENSITIVE_KEYS}
_BASE64_KEYS = {"image", "image_base64"}

_CLIENT_READY = False


class _Observation:
    def __init__(self, observation: Any | None = None) -> None:
        self._observation = observation

    def update(self, **kwargs: Any) -> None:
        if self._observation is None:
            return
        try:
            safe_kwargs = {key: safe_payload(value) for key, value in kwargs.items()}
            self._observation.update(**safe_kwargs)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse observation update skipped: %s", exc)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in _TRUTHY


def capture_payloads() -> bool:
    return _env_bool("LANGFUSE_CAPTURE_PAYLOADS", False)


def is_enabled() -> bool:
    return (
        _env_bool("LANGFUSE_TRACING_ENABLED", False)
        and bool(os.getenv("LANGFUSE_PUBLIC_KEY"))
        and bool(os.getenv("LANGFUSE_SECRET_KEY"))
    )


def _redact_text(text: str) -> str:
    redacted = _EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = _PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = _LONG_NUMBER_RE.sub("[REDACTED_NUMBER]", redacted)
    if len(redacted) > _MAX_STRING_CHARS:
        return redacted[:_MAX_STRING_CHARS] + f"...[truncated chars={len(redacted)}]"
    return redacted


def _looks_like_base64(text: str) -> bool:
    stripped = text.strip()
    if stripped.lower().startswith("data:") and "base64," in stripped.lower():
        return True
    compact = "".join(text.split())
    return (
        len(compact) >= 400
        and len(compact) % 4 == 0
        and any(char in compact for char in "+/=")
        and bool(_BASE64_RE.fullmatch(text))
    )


def summarize_text(text: str) -> dict[str, Any]:
    if _looks_like_base64(text):
        return {"redacted": "base64", "chars": len(text)}
    if not capture_payloads():
        return {"redacted": "text", "chars": len(text)}
    return {
        "chars": len(text),
        "preview": _redact_text(text[:_SUMMARY_PREVIEW_CHARS]),
    }


def _mask_value(value: Any, key: str | None = None) -> Any:
    normalized_key = (key or "").lower()
    if isinstance(value, dict):
        return {str(k): _mask_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        if normalized_key in {"images", "image_base64"}:
            return [{"redacted": "image", "chars": len(str(item))} for item in value]
        return [_mask_value(item, normalized_key) for item in value]
    if isinstance(value, bytes):
        return {"redacted": "bytes", "bytes": len(value)}
    if isinstance(value, str):
        if normalized_key in _BASE64_KEYS:
            return {"redacted": "base64", "chars": len(value)}
        if normalized_key in _SENSITIVE_KEYS or _looks_like_base64(value):
            return summarize_text(value)
        redacted = _redact_text(value)
        if not capture_payloads() and normalized_key in _PAYLOAD_KEYS:
            return summarize_text(redacted)
        return redacted
    return value


def mask_sensitive_data(data: Any, **_: Any) -> Any:
    return _mask_value(data)


def safe_payload(data: Any) -> Any:
    return mask_sensitive_data(data)


def safe_metadata(**metadata: Any) -> dict[str, Any]:
    return safe_payload({k: v for k, v in metadata.items() if v is not None})


def _propagation_metadata(metadata: dict[str, Any]) -> dict[str, str]:
    safe_meta = safe_payload(metadata)
    return {
        key: str(value)[:_MAX_STRING_CHARS]
        for key, value in safe_meta.items()
        if isinstance(value, (str, int, float, bool))
    }


def get_langfuse_client() -> Any | None:
    global _CLIENT_READY
    if not is_enabled():
        return None
    try:
        os.environ.setdefault("LANGFUSE_BASE_URL", DEFAULT_LANGFUSE_BASE_URL)
        from langfuse import Langfuse, get_client

        if not _CLIENT_READY:
            Langfuse(mask=mask_sensitive_data)
            _CLIENT_READY = True
        return get_client()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Langfuse client disabled: %s", exc)
        return None


def get_langchain_handler() -> Any | None:
    if get_langfuse_client() is None:
        return None
    try:
        from langfuse.langchain import CallbackHandler

        return CallbackHandler()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Langfuse LangChain callback disabled: %s", exc)
        return None


def langchain_config(
    *,
    run_name: str,
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    handler = get_langchain_handler()
    if handler is None:
        return {}

    all_tags = [SERVICE_NAME, *(tags or [])]
    safe_meta = safe_payload(metadata or {})
    safe_meta["langfuse_tags"] = all_tags
    if session_id:
        safe_meta["langfuse_session_id"] = session_id

    return {
        "callbacks": [handler],
        "run_name": run_name,
        "tags": all_tags,
        "metadata": safe_meta,
    }


@contextmanager
def trace_span(
    name: str,
    *,
    input_data: Any | None = None,
    metadata: dict[str, Any] | None = None,
    session_id: str | None = None,
    tags: list[str] | None = None,
) -> Iterator[_Observation]:
    client = get_langfuse_client()
    if client is None:
        yield _Observation()
        return

    all_tags = [SERVICE_NAME, *(tags or [])]
    safe_meta = safe_payload(metadata or {})
    release = os.getenv("LANGFUSE_RELEASE")

    stack = ExitStack()
    try:
        observation = stack.enter_context(
            client.start_as_current_observation(
                as_type="span",
                name=name,
                input=safe_payload(input_data),
            )
        )
        observation.update(metadata=safe_meta)

        try:
            from langfuse import propagate_attributes

            attributes = {
                "trace_name": name,
                "metadata": _propagation_metadata(safe_meta),
                "tags": all_tags,
            }
            if session_id:
                attributes["session_id"] = session_id
            if release:
                attributes["version"] = release
            stack.enter_context(propagate_attributes(**attributes))
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse attribute propagation skipped: %s", exc)
            stack.enter_context(nullcontext())
    except Exception as exc:  # noqa: BLE001
        logger.warning("Langfuse span disabled: %s", exc)
        stack.close()
        yield _Observation()
        return

    try:
        yield _Observation(observation)
    finally:
        try:
            stack.close()
        except Exception as exc:  # noqa: BLE001
            logger.debug("Langfuse span close skipped: %s", exc)


def flush() -> None:
    client = get_langfuse_client()
    if client is None:
        return
    try:
        client.flush()
    except Exception as exc:  # noqa: BLE001
        logger.debug("Langfuse flush skipped: %s", exc)
