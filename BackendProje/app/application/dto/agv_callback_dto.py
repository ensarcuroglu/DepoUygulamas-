"""AGV servisinden WMS'e gelen callback DTO'ları."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class AgvGorevTamamlamaCallbackDTO(BaseModel):
    """AgvSimService → BackendProje — robot görevi bitirdi."""

    wms_gorev_id: int = Field(..., gt=0)
    wms_gorev_tipi: Literal["Yerlestirme", "Toplama", "Transfer", "BelirsizKonum"] = "Yerlestirme"
    robot_id: str
    gerceklesen_raf_id: int = Field(..., gt=0)
    sim_baslama_tick: Optional[int] = None
    sim_tamamlanma_tick: Optional[int] = None
    rota_uzunlugu: Optional[int] = None


class AgvCallbackResponseDTO(BaseModel):
    status: Literal["tamamlandi", "zaten_tamamlandi", "iptal_edildi"]
    wms_gorev_id: int
    detay: Optional[str] = None
