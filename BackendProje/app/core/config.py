"""Uygulama feature flag konfigürasyonu.

Ortam değişkenlerinden okunur; runtime restart ile etkili olur.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List


@dataclass(frozen=True)
class FeatureFlags:
    """Feature flag'leri — .env veya ortam değişkenlerinden yüklenir."""

    # Virgülle ayrılmış depo ID'leri: "1" veya "1,3,5"
    # Boş → özellik tüm depolar için kapalı
    # Özel değer "TUMU" → tüm depolar için açık (tam rollout)
    pilot_depo_ids: List[int] = field(default_factory=list)

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        raw = os.getenv("FEATURE_URETIM_PALET_PILOT_DEPO_IDS", "").strip()
        if not raw:
            return cls(pilot_depo_ids=[])
        if raw.upper() == "TUMU":
            return cls(pilot_depo_ids=[-1])  # Sentinel: tüm depolar
        try:
            ids = [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            ids = []
        return cls(pilot_depo_ids=ids)

    def uretim_paleti_aktif_mi(self, depo_id: int | None) -> bool:
        """Kullanıcının deposu pilot kapsamında mı?

        - Admin (depo_id=None) → her zaman erişebilir
        - Sentinel -1 → tam rollout, herkes erişebilir
        - pilot_depo_ids boş → hiç kimse erişemez
        """
        if not self.pilot_depo_ids:
            return False
        if -1 in self.pilot_depo_ids:  # TUMU sentinel
            return True
        if depo_id is None:
            return True  # Admin bypass
        return depo_id in self.pilot_depo_ids


@lru_cache(maxsize=1)
def get_feature_flags() -> FeatureFlags:
    """Singleton feature flag instance — process başına bir kez yüklenir.

    Runtime değişikliği için backend restart gerekir.
    """
    return FeatureFlags.from_env()
