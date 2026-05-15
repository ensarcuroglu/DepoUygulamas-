"""DataGenService runtime configuration (pydantic-settings)."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = BASE_DIR / ".env"
ENV_FILE_ENV_VAR = "DATA_GEN_ENV_FILE"


def _resolve_env_file(env_file: str | Path | None = None) -> Path:
    selected = env_file or os.environ.get(ENV_FILE_ENV_VAR)
    if selected is None or str(selected).strip() == "":
        return DEFAULT_ENV_FILE

    path = Path(selected)
    if not path.is_absolute():
        path = BASE_DIR / path
    return path


class Settings(BaseSettings):
    """DataGenService için tipli runtime ayarları."""

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    # Backend (JWT akışı)
    backend_base_url: str = Field(
        "http://127.0.0.1:8000", alias="BACKEND_BASE_URL"
    )
    datagen_admin_username: str | None = Field(
        None, alias="DATAGEN_ADMIN_USERNAME"
    )
    datagen_admin_password: str | None = Field(
        None, alias="DATAGEN_ADMIN_PASSWORD"
    )
    jwt_refresh_buffer_sec: int = Field(
        60, alias="JWT_REFRESH_BUFFER_SEC", ge=0
    )

    # RabbitMQ
    rabbitmq_url: str = Field(
        "amqp://guest:guest@127.0.0.1:5672/", alias="RABBITMQ_URL"
    )
    rabbitmq_exchange: str = Field(
        "depo.events", alias="RABBITMQ_EXCHANGE"
    )

    # Üretim parametreleri
    default_seed: int = Field(42, alias="DEFAULT_SEED")
    locale: str = Field("tr_TR", alias="LOCALE")
    output_dir: Path = Field(
        BASE_DIR.parent / "ml_models" / "talep_tahmin" / "data" / "raw",
        alias="OUTPUT_DIR",
    )
    batch_size: int = Field(500, alias="BATCH_SIZE", ge=1)
    concurrency: int = Field(10, alias="CONCURRENCY", ge=1)

    # HTTP davranış
    http_timeout_sec: float = Field(30.0, alias="HTTP_TIMEOUT_SEC", ge=1.0)
    http_max_retries: int = Field(3, alias="HTTP_MAX_RETRIES", ge=0)

    @field_validator(
        "backend_base_url",
        "datagen_admin_username",
        "datagen_admin_password",
        "rabbitmq_url",
        "rabbitmq_exchange",
        "locale",
        mode="before",
    )
    @classmethod
    def _strip_strings(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("output_dir", mode="before")
    @classmethod
    def _resolve_output_dir(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return value
            path = Path(stripped)
            if not path.is_absolute():
                path = BASE_DIR / path
            return path
        return value


@lru_cache(maxsize=8)
def _get_settings_cached(env_file: str) -> Settings:
    return Settings(_env_file=env_file)


def get_settings(env_file: str | Path | None = None) -> Settings:
    return _get_settings_cached(str(_resolve_env_file(env_file)))


get_settings.cache_clear = _get_settings_cached.cache_clear  # type: ignore[attr-defined]
