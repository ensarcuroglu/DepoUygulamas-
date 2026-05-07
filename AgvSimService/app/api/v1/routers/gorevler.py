"""POST /api/agv/gorevler — WMS push görev kabul."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.auth import internal_api_key_verify
from app.application.dto.gorev_dto import GorevPushRequestDTO, GorevPushResponseDTO
from app.core.entities.agv_gorev import AgvGorev
from app.core.services.world import get_world

router = APIRouter(prefix="/api/agv", tags=["AGV Görev"])


@router.post(
    "/gorevler",
    response_model=GorevPushResponseDTO,
    dependencies=[Depends(internal_api_key_verify)],
)
async def gorev_kabul(req: GorevPushRequestDTO) -> GorevPushResponseDTO:
    world = get_world()
    if req.kaynak_raf_id not in world.grid.raflar:
        raise HTTPException(
            status_code=400, detail=f"Kaynak raf {req.kaynak_raf_id} grid'de yok"
        )
    if req.hedef_raf_id not in world.grid.raflar:
        raise HTTPException(
            status_code=400, detail=f"Hedef raf {req.hedef_raf_id} grid'de yok"
        )
    if req.kaynak_raf_id == req.hedef_raf_id:
        raise HTTPException(status_code=400, detail="Kaynak ve hedef raf aynı")

    agv_id = f"agv-{uuid.uuid4().hex[:8]}"
    gorev = AgvGorev(
        gorev_id=agv_id,
        wms_gorev_id=req.wms_gorev_id,
        wms_gorev_tipi=req.wms_gorev_tipi,
        kaynak_raf_id=req.kaynak_raf_id,
        hedef_raf_id=req.hedef_raf_id,
        palet_id=req.palet_id,
        oncelik=req.oncelik,
    )
    async with world.lock:
        world.gorev_kuyrugu.append(gorev)
        kuyruk_uzunlugu = len(world.gorev_kuyrugu)

    return GorevPushResponseDTO(
        kabul_edildi=True,
        agv_gorev_id=agv_id,
        kuyruk_uzunlugu=kuyruk_uzunlugu,
    )
