"""ERP integration configuration facade.

The public ErpConfig/PaletVeriKaynagi API is kept for existing services, while
values are sourced from the central Settings object.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.core.config import Settings, load_settings


class PaletVeriKaynagi(str, Enum):
    """Palet bilgi kaynagi secenekleri."""

    LOCAL = "LOCAL"
    ERP = "ERP"
    MOCK = "MOCK"


@dataclass(frozen=True)
class ErpConfig:
    """ERP baglanti ayarlari."""

    palet_veri_kaynagi: PaletVeriKaynagi
    erp_api_url: Optional[str]
    erp_api_key: Optional[str]
    erp_timeout: int

    @classmethod
    def from_settings(cls, settings: Settings) -> "ErpConfig":
        kaynak_str = settings.palet_veri_kaynagi.upper()
        try:
            kaynak = PaletVeriKaynagi(kaynak_str)
        except ValueError:
            kaynak = PaletVeriKaynagi.LOCAL

        return cls(
            palet_veri_kaynagi=kaynak,
            erp_api_url=settings.erp_api_url,
            erp_api_key=settings.erp_api_key,
            erp_timeout=settings.erp_timeout,
        )

    @classmethod
    def from_env(cls) -> "ErpConfig":
        """Preserve old env-only behavior for unit tests and direct callers."""

        return cls.from_settings(load_settings(use_env_file=False))

    def erp_yapilandirildi_mi(self) -> bool:
        return bool(self.erp_api_url and self.erp_api_key)
