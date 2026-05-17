from __future__ import annotations

import langfuse_tracing as tracing


def test_langfuse_disabled_returns_noop_config(monkeypatch):
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")

    assert tracing.is_enabled() is False
    assert tracing.langchain_config(run_name="test") == {}

    with tracing.trace_span("test") as span:
        span.update(output={"ok": True})


def test_langchain_config_includes_callback_when_enabled(monkeypatch):
    callback = object()
    monkeypatch.setattr(tracing, "is_enabled", lambda: True)
    monkeypatch.setattr(tracing, "get_langchain_handler", lambda: callback)

    config = tracing.langchain_config(
        run_name="test-run",
        metadata={"route": "sql"},
        session_id="session-1",
        tags=["sql"],
    )

    assert config["callbacks"] == [callback]
    assert config["run_name"] == "test-run"
    assert config["metadata"]["langfuse_session_id"] == "session-1"
    assert "wms-ai" in config["tags"]


def test_masking_redacts_pii_and_large_payload(monkeypatch):
    monkeypatch.setenv("LANGFUSE_CAPTURE_PAYLOADS", "false")

    masked = tracing.safe_payload(
        {
            "email": "ali@example.com",
            "phone": "+90 555 123 45 67",
            "content": "x" * 500,
        }
    )

    assert masked["email"] == "[REDACTED_EMAIL]"
    assert masked["phone"] == "[REDACTED_PHONE]"
    assert masked["content"]["redacted"] == "text"


def test_trace_span_swallows_langfuse_errors(monkeypatch):
    class BrokenClient:
        def start_as_current_observation(self, **_kwargs):
            raise RuntimeError("langfuse unavailable")

    monkeypatch.setattr(tracing, "get_langfuse_client", lambda: BrokenClient())

    with tracing.trace_span("broken") as span:
        span.update(output={"ok": True})
