"""Dashboard Use Case'leri."""

from __future__ import annotations

from app.core.repositories.dashboard_repository import IDashboardRepository
from app.application.dto.dashboard_dto import DashboardStatsResponseDTO


class DashboardIstatistikGetirUseCase:
    """Dashboard istatistiklerini getirir."""

    def __init__(self, dashboard_repo: IDashboardRepository):
        self._dashboard_repo = dashboard_repo

    def execute(self) -> DashboardStatsResponseDTO:
        istatistik = self._dashboard_repo.istatistik_getir()
        return DashboardStatsResponseDTO.from_entity(istatistik)
