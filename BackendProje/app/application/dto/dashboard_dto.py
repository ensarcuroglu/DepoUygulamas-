"""Dashboard veri transfer nesneleri (DTO)."""

from __future__ import annotations

from pydantic import BaseModel

from app.core.repositories.dashboard_repository import DashboardIstatistik


class StokAkisiOzetDTO(BaseModel):
    day: str
    giris: int
    cikis: int


class DashboardStatsResponseDTO(BaseModel):
    toplam_urun: int
    kritik_stok_sayisi: int
    bugunku_hareket: int
    toplam_deger: float
    stok_akisi: list[StokAkisiOzetDTO] = []

    @classmethod
    def from_entity(cls, vo: DashboardIstatistik) -> "DashboardStatsResponseDTO":
        stok_akisi_dto = [StokAkisiOzetDTO(**item) for item in vo.stok_akisi] if hasattr(vo, "stok_akisi") else []
        return cls(
            toplam_urun=vo.toplam_urun,
            kritik_stok_sayisi=vo.kritik_stok_sayisi,
            bugunku_hareket=vo.bugunku_hareket,
            toplam_deger=vo.toplam_deger,
            stok_akisi=stok_akisi_dto
        )
