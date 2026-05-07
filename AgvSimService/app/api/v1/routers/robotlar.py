"""GET /api/agv/robotlar — anlık robot snapshot'ı."""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dto.robot_dto import RobotSnapshotResponseDTO
from app.core.services.world import get_world

router = APIRouter(prefix="/api/agv", tags=["AGV Robot"])


@router.get("/robotlar", response_model=RobotSnapshotResponseDTO)
def robotlari_listele() -> dict:
    world = get_world()
    return {"tick_no": world.tick_no, "robotlar": world.robot_dict_listesi()}


@router.get("/grid", tags=["AGV Robot"])
def grid_snapshot() -> dict:
    """Frontend ilk yüklemesi için grid + raf bilgisi (statik)."""
    world = get_world()
    return world.snapshot_tam()
