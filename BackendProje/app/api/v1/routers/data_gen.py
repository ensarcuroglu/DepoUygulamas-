"""DataGenService proxy router."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.core.auth import require_role
from app.core.config import Settings, get_settings
from app.infrastructure.services.data_gen_client import DataGenClient
from models import Kullanici

router = APIRouter(prefix="/api/data-gen", tags=["DataGen"])

TargetName = Literal["rest", "rabbit", "file"]


class ScenarioRunRequest(BaseModel):
    """DataGenService ortak senaryo calistirma parametreleri."""

    model_config = ConfigDict(extra="forbid")

    count: int | None = Field(default=None, ge=1)
    seed: int | None = None
    target: TargetName | None = None
    batch_size: int | None = Field(default=None, ge=1)
    concurrency: int | None = Field(default=None, ge=1)


SCENARIO_METADATA: dict[str, dict[str, Any]] = {
    "seed_baseline": {
        "name": "seed_baseline",
        "label": "Temel Seed Verisi",
        "description": "Raf, urun, lot ve palet zincirini Backend REST API uzerinden basar.",
        "default_target": "rest",
        "allowed_targets": ["rest"],
        "risk_level": "high",
        "confirmation_required": True,
        "count_label": "Toplam seed olcegi",
    },
    "task_load": {
        "name": "task_load",
        "label": "Gorev Yuk Testi",
        "description": "Toplama gorevleri veya LMS event hatti icin sentetik yuk uretir.",
        "default_target": "rest",
        "allowed_targets": ["rest", "rabbit"],
        "risk_level": "medium",
        "confirmation_required": True,
        "count_label": "Gorev/event adedi",
        "target_notes": {
            "rabbit": "Rabbit hedefi saf yuk testidir; anlamli LMS akisi icin rest tercih edilir.",
        },
    },
    "timeseries_history": {
        "name": "timeseries_history",
        "label": "Talep Zaman Serisi",
        "description": "ML egitimi icin parquet/csv talep gecmisi dosyasi uretir.",
        "default_target": "file",
        "allowed_targets": ["file"],
        "risk_level": "low",
        "confirmation_required": False,
        "count_label": "Urun adedi",
    },
    "agv_traffic": {
        "name": "agv_traffic",
        "label": "AGV Trafik Uretimi",
        "description": "Backend yerlestirme gorevi ucuna yogun trafik gonderir.",
        "default_target": "rest",
        "allowed_targets": ["rest"],
        "risk_level": "high",
        "confirmation_required": True,
        "count_label": "Yerlestirme gorevi adedi",
    },
}


def _ensure_enabled(settings: Settings) -> None:
    if not settings.feature_data_gen_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DataGen ozelligi devre disi.",
        )


def _get_client(settings: Settings = Depends(get_settings)) -> DataGenClient:
    _ensure_enabled(settings)
    return DataGenClient(settings)


@router.get("/metadata")
def metadata(
    _client: DataGenClient = Depends(_get_client),
    _current_user: Kullanici = Depends(require_role("admin")),
) -> dict[str, Any]:
    return {
        "scenarios": list(SCENARIO_METADATA.values()),
        "defaults": {
            "seed": 42,
            "batch_size": 500,
            "concurrency": 10,
        },
    }


@router.get("/healthz")
def healthz(
    client: DataGenClient = Depends(_get_client),
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    return client.healthz()


@router.post("/scenarios/{name}/run")
def run_scenario(
    name: str,
    request: ScenarioRunRequest,
    client: DataGenClient = Depends(_get_client),
    _current_user: Kullanici = Depends(require_role("admin")),
) -> Any:
    if name not in SCENARIO_METADATA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Bilinmeyen senaryo: {name!r}",
        )

    payload = request.model_dump(exclude_none=True)
    target = payload.get("target") or SCENARIO_METADATA[name]["default_target"]
    allowed_targets = SCENARIO_METADATA[name]["allowed_targets"]
    if target not in allowed_targets:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Senaryo {name!r} icin target {target!r} izinli degil. "
                f"Izinli: {allowed_targets}"
            ),
        )

    payload["target"] = target
    return client.run_scenario(name, payload)
