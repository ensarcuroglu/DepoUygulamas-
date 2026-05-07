"""AGV entegrasyonu DI factory'leri.

Faz 3 — feature flag arkasındaki AGV dispatcher + AGV callback use case'i.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.application.use_cases.agv_yerlestirme_tamamla_use_case import (
    AgvYerlestirmeTamamlaUseCase,
)
from app.core.config import get_settings
from app.core.services.agv_dispatcher import (
    IAgvDispatcher,
    NoOpAgvDispatcher,
)
from app.infrastructure.services.http_agv_dispatcher import HttpAgvDispatcher
from database import get_db
from models import Kullanici


@lru_cache(maxsize=1)
def _build_dispatcher() -> IAgvDispatcher:
    settings = get_settings()
    pilot_ids = settings.feature_agv_dispatch_depo_id_list
    if not pilot_ids:
        return NoOpAgvDispatcher()
    return HttpAgvDispatcher(
        base_url=settings.agv_sim_service_url,
        api_key=settings.internal_api_key,
        pilot_depo_ids=pilot_ids,
        timeout=settings.agv_sim_service_timeout,
    )


def get_agv_dispatcher() -> IAgvDispatcher:
    """FastAPI `Depends()` içinde kullanılır. Singleton."""
    return _build_dispatcher()


def reset_agv_dispatcher_cache() -> None:
    """Yapılandırma değişikliği sonrası test/runtime için."""
    _build_dispatcher.cache_clear()


# ── Synthetic AGV kullanıcı id resolver ───────────────────────────────────────

AGV_KULLANICI_ADI = "agv-system"


def get_agv_kullanici_id(db: Session = Depends(get_db)) -> int:
    """Synthetic AGV system user'ın id'sini döner.

    `seed_agv_user.py` çalıştırılmamışsa 503 döner — operatör müdahale gerek.
    """
    user = (
        db.query(Kullanici)
        .filter(Kullanici.kullanici_adi == AGV_KULLANICI_ADI)
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                f"Synthetic AGV kullanici ({AGV_KULLANICI_ADI}) tanimli degil. "
                "seed_agv_user.py calistirilmali."
            ),
        )
    return user.id


# ── AGV Yerleştirme Tamamla Use Case factory ──────────────────────────────────
#
# Not: depo_envanter_di top-level olarak agv_di'yi lazy-import ediyor (içeride
# `_get_agv_dispatcher_lazy` fonksiyonu üzerinden), bu yüzden ters yön
# (agv_di → depo_envanter_di) güvenli — module body'leri sırayla tamamlanır.

from app.infrastructure.di.modules.depo_envanter_di import (  # noqa: E402
    get_yerlestirme_gorevi_repo,
    get_yerlestirme_gorevi_tamamla_uc,
)


def get_agv_yerlestirme_tamamla_uc(
    repo=Depends(get_yerlestirme_gorevi_repo),
    tamamla_uc=Depends(get_yerlestirme_gorevi_tamamla_uc),
) -> AgvYerlestirmeTamamlaUseCase:
    return AgvYerlestirmeTamamlaUseCase(repo, tamamla_uc)
