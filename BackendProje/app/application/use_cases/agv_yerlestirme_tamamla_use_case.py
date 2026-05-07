"""AGV callback use case — robot bitirdiği görevi WMS'te kapat.

Tasarım:
- AGV görev kuyruktan çekildikten sonra görev WMS tarafında muhtemelen
  hâlâ BEKLIYOR durumunda (insan operatör ata/baslat çağırmadı).
- Bu use case görev durumunu zorla DEVAM_EDIYOR'a kadar getirir, sonra
  mevcut `YerlestirmeGoreviTamamlaUseCase`'i delege eder. Böylece palet
  konum güncelleme, mal kabul kapanma kontrolü, performans event'i gibi
  tüm iş kuralları tek noktada (mevcut tamamla use case) çalışır.
- İdempotent: görev zaten TAMAMLANDI ya da IPTAL_EDILDI ise no-op döner.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.application.dto.agv_callback_dto import (
    AgvCallbackResponseDTO,
    AgvGorevTamamlamaCallbackDTO,
)
from app.application.dto.yerlestirme_gorevi_dto import (
    YerlestirmeGoreviTamamlaRequestDTO,
)
from app.core.entities.yerlestirme_gorevi import GorevDurum
from app.core.exceptions import KayitBulunamadiError
from app.core.repositories.yerlestirme_gorevi_repository import (
    IYerlestirmeGoreviRepository,
)

if TYPE_CHECKING:  # circular import koruması (DI factory'de gerçek tip)
    from app.application.use_cases.yerlestirme_gorevi_use_cases import (
        YerlestirmeGoreviTamamlaUseCase,
    )

log = logging.getLogger(__name__)


class AgvYerlestirmeTamamlaUseCase:
    def __init__(
        self,
        repo: IYerlestirmeGoreviRepository,
        tamamla_uc: "YerlestirmeGoreviTamamlaUseCase",
    ) -> None:
        self._repo = repo
        self._tamamla_uc = tamamla_uc

    def execute(
        self,
        dto: AgvGorevTamamlamaCallbackDTO,
        agv_kullanici_id: int,
    ) -> AgvCallbackResponseDTO:
        gorev = self._repo.getir_id_ile(dto.wms_gorev_id)
        if not gorev:
            raise KayitBulunamadiError("YerlestirmeGorevi", dto.wms_gorev_id)

        # Idempotency — görev zaten kapanmışsa OK dön.
        if gorev.durum == GorevDurum.TAMAMLANDI:
            return AgvCallbackResponseDTO(
                status="zaten_tamamlandi",
                wms_gorev_id=gorev.id,
                detay=f"Robot {dto.robot_id}",
            )
        if gorev.durum == GorevDurum.IPTAL_EDILDI:
            return AgvCallbackResponseDTO(
                status="iptal_edildi",
                wms_gorev_id=gorev.id,
                detay="Görev önceden iptal edildi",
            )

        # State machine'i zorla TAMAMLANDI'ya yakın getir.
        # Entity'nin kendi metodları geçiş tablosunu doğrular.
        if gorev.durum == GorevDurum.BEKLIYOR:
            gorev.ata(agv_kullanici_id)
        if gorev.durum == GorevDurum.ATANDI:
            gorev.baslat()
        # DEVAM_EDIYOR'a ulaştığımız anda persist et — tamamla use case
        # repo'dan yeniden okuyacak, güncel state görsün.
        self._repo.guncelle(gorev)

        # Mevcut tamamla use case devreye girer (palet konum, mal kabul, perf).
        self._tamamla_uc.execute(
            gorev.id,
            YerlestirmeGoreviTamamlaRequestDTO(
                gerceklesen_raf_id=dto.gerceklesen_raf_id,
            ),
            kullanici_id=agv_kullanici_id,
        )

        log.info(
            "AGV callback tamamlandi gorev=%s robot=%s raf=%s",
            gorev.id,
            dto.robot_id,
            dto.gerceklesen_raf_id,
        )
        return AgvCallbackResponseDTO(
            status="tamamlandi",
            wms_gorev_id=gorev.id,
        )
