"""ERP entegrasyon konfigurasyonu.

.env dosyasindan ERP baglanti ayarlarini ve palet veri kaynagi
secimini okur. ERP gercek entegrasyonda sadece bu degerler doldurulur.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PaletVeriKaynagi(str, Enum):
    """Palet bilgi kaynagi secenekleri."""

    LOCAL = "LOCAL"  # IrsaliyePaletVeriKaynagiService (mevcut)
    ERP = "ERP"      # ErpPaletVeriKaynagiService (gercek ERP)
    MOCK = "MOCK"    # MockErpPaletVeriKaynagiService (demo/dev)


@dataclass(frozen=True)
class ErpConfig:
    """ERP baglanti ayarlari — .env'den okunur."""

    palet_veri_kaynagi: PaletVeriKaynagi
    erp_api_url: Optional[str]
    erp_api_key: Optional[str]
    erp_timeout: int  # saniye

    @classmethod
    def from_env(cls) -> ErpConfig:
        """Ortam degiskenlerinden config olusturur."""
        kaynak_str = os.getenv("PALET_VERI_KAYNAGI", "LOCAL").upper()
        try:
            kaynak = PaletVeriKaynagi(kaynak_str)
        except ValueError:
            kaynak = PaletVeriKaynagi.LOCAL

        return cls(
            palet_veri_kaynagi=kaynak,
            erp_api_url=os.getenv("ERP_API_URL"),
            erp_api_key=os.getenv("ERP_API_KEY"),
            erp_timeout=int(os.getenv("ERP_TIMEOUT", "30")),
        )

    def erp_yapilandirildi_mi(self) -> bool:
        """ERP API URL ve KEY dolu mu kontrol eder."""
        return bool(self.erp_api_url and self.erp_api_key)
