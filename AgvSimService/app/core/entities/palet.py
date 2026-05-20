"""Palet runtime durumu — görsel/sim katmanı.

AgvSimService DB'ye yazmaz; palet kaydı yalnızca görselleştirme + event akışı
içindir. BackendProje source-of-truth olarak kalır.

Yaşam döngüsü:
    KAYNAKTA_BEKLIYOR  → görev kuyruğa alınınca; kaynak rafın koordinatında.
    ROBOT_UZERINDE     → robot kaynaktan paleti aldığında (`palet_alindi`).
    HEDEFTE_BIRAKILDI  → robot paleti hedefe bıraktığında (`palet_birakildi`).
    BILINMIYOR         → palet kaydı silindiyse fallback (kullanılmıyor şu anda).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PaletDurum(str, Enum):
    KAYNAKTA_BEKLIYOR = "KaynaktaBekliyor"
    ROBOT_UZERINDE = "RobotUzerinde"
    HEDEFTE_BIRAKILDI = "HedefteBirakildi"
    BILINMIYOR = "Bilinmiyor"


@dataclass
class Palet:
    """Bir palet için runtime kaydı.

    `palet_key` — paleti hem sim hem frontend tarafında stabil kimlendirir.
    `palet_id` BackendProje WMS palet id'sidir (opsiyonel). None ise palet_key
    görev tabanlı üretilir.
    """

    palet_key: str
    palet_id: Optional[int]
    durum: PaletDurum
    x: int                # KAYNAKTA_BEKLIYOR / HEDEFTE_BIRAKILDI iken sabit raf koordinatı
    y: int
    kaynak_raf_id: int
    hedef_raf_id: int
    robot_id: Optional[str] = None        # ROBOT_UZERINDE iken set
    gorev_id: Optional[str] = None        # bağlı AGV görev id'si
