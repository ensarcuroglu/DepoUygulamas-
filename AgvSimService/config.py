"""AgvSimService settings — pydantic-settings ile .env okuma."""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # WMS (BackendProje) bağlantısı — AGV görev callback'leri için
    WMS_BASE_URL: str = "http://127.0.0.1:8000"

    # Servisler arası kimlik (BackendProje ile aynı değer olmalı)
    INTERNAL_API_KEY: str = ""

    # Tick loop frekansı (Hz). 5-10 arası önerilir.
    TICK_HZ: int = 5

    # CORS — frontend'in bağlanabileceği origin'ler
    CORS_ALLOW_ORIGINS: str = "https://localhost:5173"

    # Faz 1: depo grid kaynağı. "json" = elle hazırlanmış dosya, "wms" = BackendProje API.
    GRID_KAYNAGI: str = "json"
    GRID_JSON_PATH: str = "./data/depo_1_grid.json"

    # WS broadcast yavaş client koruması — kuyruk bu sınırı aşarsa bağlantı kapatılır
    WS_MAX_QUEUE: int = 32

    @property
    def cors_allow_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]


settings = Settings()
