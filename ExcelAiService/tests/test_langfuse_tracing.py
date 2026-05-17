from __future__ import annotations

from app.infrastructure.observability import langfuse_tracing as tracing


def test_langfuse_disabled_returns_noop_config(monkeypatch):
    monkeypatch.setenv("LANGFUSE_TRACING_ENABLED", "false")

    assert tracing.is_enabled() is False
    assert tracing.langchain_config(run_name="excel-test") == {}


def test_langchain_config_includes_callback_when_enabled(monkeypatch):
    callback = object()
    monkeypatch.setattr(tracing, "is_enabled", lambda: True)
    monkeypatch.setattr(tracing, "get_langchain_handler", lambda: callback)

    config = tracing.langchain_config(
        run_name="excel-agent",
        metadata={"operation": "pandas_agent"},
        tags=["excel", "qa"],
    )

    assert config["callbacks"] == [callback]
    assert config["run_name"] == "excel-agent"
    assert "excel-ai" in config["tags"]
    assert config["metadata"]["operation"] == "pandas_agent"
