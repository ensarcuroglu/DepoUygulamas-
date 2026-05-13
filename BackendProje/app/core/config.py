"""Central application configuration.

All runtime configuration is loaded through pydantic-settings while keeping the
existing environment variable names for backwards compatibility.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = BASE_DIR / ".env"
ENV_FILE_ENV_VAR = "DEPO_APP_ENV_FILE"


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
    """Typed settings loaded from environment variables and a .env file."""

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    db_user: str = Field("root", alias="DB_USER")
    db_password: str = Field("", alias="DB_PASSWORD")
    db_host: str = Field("localhost", alias="DB_HOST")
    db_port: int = Field(3306, alias="DB_PORT", ge=1, le=65535)
    db_name: str = Field("depo_yonetim", alias="DB_NAME")

    jwt_secret_key: Optional[str] = Field(None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        480,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=1,
    )
    refresh_token_expire_days: int = Field(
        7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS",
        ge=1,
    )

    cors_allow_origins_raw: str = Field(
        "https://localhost:5173,http://localhost:3000",
        alias="CORS_ALLOW_ORIGINS",
    )

    smtp_host: Optional[str] = Field(None, alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT", ge=1, le=65535)
    smtp_user: Optional[str] = Field(None, alias="SMTP_USER")
    smtp_password: Optional[str] = Field(None, alias="SMTP_PASSWORD")
    smtp_from: Optional[str] = Field("noreply@depoyonetim.com", alias="SMTP_FROM")

    putaway_timeout: int = Field(60, alias="PUTAWAY_TIMEOUT", ge=1)
    staging_uyari_esik_saat: int = Field(
        24,
        alias="STAGING_UYARI_ESIK_SAAT",
        ge=1,
    )

    feature_uretim_palet_pilot_depo_ids: str = Field(
        "",
        alias="FEATURE_URETIM_PALET_PILOT_DEPO_IDS",
    )

    feature_agv_dispatch_depo_ids: str = Field(
        "",
        alias="FEATURE_AGV_DISPATCH_DEPO_IDS",
    )

    feature_doc_ai_pilot_depo_ids: str = Field(
        "",
        alias="FEATURE_DOC_AI_PILOT_DEPO_IDS",
    )

    agv_sim_service_url: str = Field(
        "http://127.0.0.1:8002",
        alias="AGV_SIM_SERVICE_URL",
    )
    agv_sim_service_timeout: float = Field(
        2.0,
        alias="AGV_SIM_SERVICE_TIMEOUT",
        ge=0.1,
    )
    doc_ai_service_url: str = Field(
        "http://127.0.0.1:8003",
        alias="DOC_AI_SERVICE_URL",
    )
    doc_ai_service_timeout: float = Field(
        120.0,
        alias="DOC_AI_SERVICE_TIMEOUT",
        ge=1.0,
    )

    internal_api_key: Optional[str] = Field(None, alias="INTERNAL_API_KEY")

    palet_veri_kaynagi: str = Field("LOCAL", alias="PALET_VERI_KAYNAGI")
    erp_api_url: Optional[str] = Field(None, alias="ERP_API_URL")
    erp_api_key: Optional[str] = Field(None, alias="ERP_API_KEY")
    erp_timeout: int = Field(30, alias="ERP_TIMEOUT", ge=1)

    clean_test_data_allowed_dbs: str = Field(
        "",
        alias="CLEAN_TEST_DATA_ALLOWED_DBS",
    )

    wms_ai_service_url: str = Field(
        "http://localhost:8001",
        alias="WMS_AI_SERVICE_URL",
    )
    wms_ai_service_timeout: float = Field(
        180.0,
        alias="WMS_AI_SERVICE_TIMEOUT",
        ge=1.0,
    )

    rabbitmq_enabled: bool = Field(False, alias="RABBITMQ_ENABLED")
    rabbitmq_url: str = Field(
        "amqp://guest:guest@localhost:5672/",
        alias="RABBITMQ_URL",
    )
    rabbitmq_exchange: str = Field("depo.events", alias="RABBITMQ_EXCHANGE")
    rabbitmq_queue: str = Field(
        "depo.lms.operator_metrikleri",
        alias="RABBITMQ_QUEUE",
    )
    rabbitmq_dlx: str = Field("depo.events.dlx", alias="RABBITMQ_DLX")
    rabbitmq_prefetch: int = Field(
        20,
        alias="RABBITMQ_PREFETCH",
        ge=1,
        le=10000,
    )
    rabbitmq_relay_batch_size: int = Field(
        100,
        alias="RABBITMQ_RELAY_BATCH_SIZE",
        ge=1,
        le=10000,
    )

    @field_validator("db_user", "db_host", "db_name")
    @classmethod
    def _required_str(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("value must not be empty")
        return stripped

    @field_validator(
        "jwt_secret_key",
        "smtp_host",
        "smtp_user",
        "smtp_password",
        "smtp_from",
        "erp_api_url",
        "erp_api_key",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @field_validator("jwt_algorithm", "palet_veri_kaynagi", mode="before")
    @classmethod
    def _upper_or_default(cls, value: object, info) -> object:
        if isinstance(value, str):
            stripped = value.strip().upper()
            if stripped:
                return stripped
        return "HS256" if info.field_name == "jwt_algorithm" else "LOCAL"

    @property
    def sqlalchemy_database_url(self) -> str:
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": "utf8mb4"},
        ).render_as_string(hide_password=False)

    @property
    def cors_allow_origins(self) -> list[str]:
        return _parse_csv(self.cors_allow_origins_raw)

    @property
    def feature_uretim_palet_pilot_depo_id_list(self) -> list[int]:
        raw = self.feature_uretim_palet_pilot_depo_ids.strip()
        if not raw:
            return []
        if raw.upper() == "TUMU":
            return [-1]
        try:
            return [int(item.strip()) for item in raw.split(",") if item.strip()]
        except ValueError:
            return []

    @property
    def feature_agv_dispatch_depo_id_list(self) -> list[int]:
        raw = self.feature_agv_dispatch_depo_ids.strip()
        if not raw:
            return []
        if raw.upper() == "TUMU":
            return [-1]
        try:
            return [int(item.strip()) for item in raw.split(",") if item.strip()]
        except ValueError:
            return []

    @property
    def feature_doc_ai_pilot_depo_id_list(self) -> list[int]:
        raw = self.feature_doc_ai_pilot_depo_ids.strip()
        if not raw:
            return []
        if raw.upper() == "TUMU":
            return [-1]
        try:
            return [int(item.strip()) for item in raw.split(",") if item.strip()]
        except ValueError:
            return []

    @property
    def clean_test_data_allowed_db_names(self) -> list[str]:
        return [item.lower() for item in _parse_csv(self.clean_test_data_allowed_dbs)]

    def require_jwt_secret_key(self) -> str:
        if not self.jwt_secret_key:
            raise RuntimeError(
                "JWT_SECRET_KEY ortam degiskeni ayarlanmamis. "
                "Lutfen .env dosyasina JWT_SECRET_KEY ekleyin."
            )
        if len(self.jwt_secret_key) < 32:
            raise RuntimeError("JWT_SECRET_KEY en az 32 karakter olmalidir.")
        return self.jwt_secret_key


def load_settings(
    env_file: str | Path | None = None,
    *,
    use_env_file: bool = True,
) -> Settings:
    """Create an uncached Settings instance.

    use_env_file=False preserves old from_env-style tests that intentionally
    patch os.environ without reading BackendProje/.env.
    """

    if not use_env_file:
        return Settings(_env_file=None)
    return Settings(_env_file=_resolve_env_file(env_file))


@lru_cache(maxsize=8)
def _get_settings_cached(env_file: str) -> Settings:
    return Settings(_env_file=env_file)


def get_settings(env_file: str | Path | None = None) -> Settings:
    return _get_settings_cached(str(_resolve_env_file(env_file)))


get_settings.cache_clear = _get_settings_cached.cache_clear  # type: ignore[attr-defined]


@dataclass(frozen=True)
class FeatureFlags:
    """Feature flags loaded through Settings."""

    # Empty list: feature is disabled for every warehouse.
    # [-1]: full rollout ("TUMU").
    pilot_depo_ids: list[int] = field(default_factory=list)
    agv_dispatch_depo_ids: list[int] = field(default_factory=list)
    doc_ai_pilot_depo_ids: list[int] = field(default_factory=list)

    @classmethod
    def from_settings(cls, settings: Settings) -> "FeatureFlags":
        return cls(
            pilot_depo_ids=settings.feature_uretim_palet_pilot_depo_id_list,
            agv_dispatch_depo_ids=settings.feature_agv_dispatch_depo_id_list,
            doc_ai_pilot_depo_ids=settings.feature_doc_ai_pilot_depo_id_list,
        )

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        return cls.from_settings(load_settings(use_env_file=False))

    def uretim_paleti_aktif_mi(self, depo_id: int | None) -> bool:
        return self._depo_aktif_mi(self.pilot_depo_ids, depo_id)

    def agv_dispatch_aktif_mi(self, depo_id: int | None) -> bool:
        return self._depo_aktif_mi(self.agv_dispatch_depo_ids, depo_id)

    def doc_ai_aktif_mi(self, depo_id: int | None) -> bool:
        return self._depo_aktif_mi(self.doc_ai_pilot_depo_ids, depo_id)

    @staticmethod
    def _depo_aktif_mi(depo_listesi: list[int], depo_id: int | None) -> bool:
        if not depo_listesi:
            return False
        if -1 in depo_listesi:
            return True
        if depo_id is None:
            return False
        return depo_id in depo_listesi


@lru_cache(maxsize=1)
def get_feature_flags() -> FeatureFlags:
    """Singleton feature flag instance; restart/cache clear reloads values."""

    return FeatureFlags.from_settings(load_settings())
