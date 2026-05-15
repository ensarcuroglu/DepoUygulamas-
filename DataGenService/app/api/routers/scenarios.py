"""Senaryo çalıştırma HTTP yüzeyi."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import get_settings
from app.scenarios import TargetNotAllowedError
from app.scenarios.runner import (
    ScenarioRunRequest,
    result_to_jsonable,
    run_scenario,
)

router = APIRouter(prefix="/scenarios", tags=["Scenarios"])


@router.post("/{name}/run")
async def run_scenario_endpoint(
    name: str, body: ScenarioRunRequest
) -> dict[str, object]:
    """İstenen senaryoyu çalıştırır ve JSON özet döner."""

    try:
        result = await run_scenario(name, body, settings=get_settings())
    except TargetNotAllowedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    return result_to_jsonable(result)

