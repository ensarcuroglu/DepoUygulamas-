"""AssistantAiService runtime configuration."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = BASE_DIR / ".env"
ENV_FILE_ENV_VAR = "ASSISTANT_AI_ENV_FILE"


def _resolve_env_file(env_file: str | Path | None = None) -> Path:
    selected = env_file or os.environ.get(ENV_FILE_ENV_VAR)
    if selected is None or str(selected).strip() == "":
        return DEFAULT_ENV_FILE

    path = Path(selected)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


def _parse_csv(value: str | None) -> list[str]:
    if value is None:
        return []

    raw = value.strip()
    if not raw:
        return []

    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except json.JSONDecodeError:
            pass

    return [item.strip() for item in raw.split(",") if item.strip()]


class Settings(BaseSettings):
    """Typed settings loaded from environment variables and AssistantAiService/.env."""

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    internal_api_key: str | None = Field(None, alias="INTERNAL_API_KEY")

    ollama_base_url: str = Field("http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    assistant_llm_model: str = Field("qwen2.5:7b-instruct", alias="ASSISTANT_LLM_MODEL")
    llm_timeout: float = Field(120.0, alias="LLM_TIMEOUT", ge=1.0)

    backend_base_url: str = Field("http://127.0.0.1:8000", alias="BACKEND_BASE_URL")
    sqlite_checkpoint_path: str = Field(
        "/data/assistant_state.sqlite",
        alias="SQLITE_CHECKPOINT_PATH",
    )

    cors_allow_origins_raw: str = Field(
        "https://localhost:5173",
        alias="CORS_ALLOW_ORIGINS",
    )

    @field_validator(
        "internal_api_key",
        "ollama_base_url",
        "assistant_llm_model",
        "backend_base_url",
        "sqlite_checkpoint_path",
        "cors_allow_origins_raw",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @property
    def cors_allow_origins(self) -> list[str]:
        return _parse_csv(self.cors_allow_origins_raw)


def load_settings(
    env_file: str | Path | None = None,
    *,
    use_env_file: bool = True,
) -> Settings:
    if not use_env_file:
        return Settings(_env_file=None)
    return Settings(_env_file=_resolve_env_file(env_file))


@lru_cache(maxsize=8)
def _get_settings_cached(env_file: str) -> Settings:
    return Settings(_env_file=env_file)


def get_settings(env_file: str | Path | None = None) -> Settings:
    return _get_settings_cached(str(_resolve_env_file(env_file)))


get_settings.cache_clear = _get_settings_cached.cache_clear  # type: ignore[attr-defined]
