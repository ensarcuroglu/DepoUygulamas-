"""Dashboard veri transfer nesneleri (DTO)."""

from __future__ import annotations

from pydantic import BaseModel

from app.core.repositories.dashboard_repository import DashboardIstatistik


class DashboardStatsResponseDTO(BaseModel):
    toplam_urun: int
    kritik_stok_sayisi: int
    bugunku_hareket: int
    toplam_deger: float

    @classmethod
    def from_entity(cls, vo: DashboardIstatistik) -> "DashboardStatsResponseDTO":
        return cls(
            toplam_urun=vo.toplam_urun,
            kritik_stok_sayisi=vo.kritik_stok_sayisi,
            bugunku_hareket=vo.bugunku_hareket,
            toplam_deger=vo.toplam_deger,
        )
