from __future__ import annotations

from app.infrastructure.observability import langfuse_tracing as tracing


def test_langfuse_disabled_span_is_noop(monkeypatch):
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")

    assert tracing.is_enabled() is False
    with tracing.trace_span("doc-test") as span:
        span.update(output={"ok": True})
    with tracing.trace_generation("doc-gen", model="fake-model") as generation:
        generation.update(output={"ok": True})


def test_vlm_base64_is_never_captured(monkeypatch):
    monkeypatch.setenv("LANGFUSE_CAPTURE_PAYLOADS", "true")
    image_payload = "a" * 800

    masked = tracing.safe_payload({"image_base64": image_payload})

    assert masked["image_base64"]["redacted"] == "base64"
    assert masked["image_base64"]["chars"] == len(image_payload)


def test_generation_swallows_langfuse_errors(monkeypatch):
    class BrokenClient:
        def start_as_current_observation(self, **_kwargs):
            raise RuntimeError("langfuse unavailable")

    monkeypatch.setattr(tracing, "get_langfuse_client", lambda: BrokenClient())

    with tracing.trace_generation("broken", model="fake-model") as generation:
        generation.update(output={"ok": True})
