"""Dashboard API Router — Clean Architecture (Thin Controller)."""

from fastapi import APIRouter, Depends

from app.core.auth import require_role
from models import Kullanici

from app.infrastructure.di.container import get_dashboard_istatistik_uc
from app.application.dto.dashboard_dto import DashboardStatsResponseDTO
from app.application.use_cases.dashboard_use_cases import DashboardIstatistikGetirUseCase

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardStatsResponseDTO)
def dashboard_istatistikleri(
    current_user: Kullanici = Depends(require_role("admin")),
    uc: DashboardIstatistikGetirUseCase = Depends(get_dashboard_istatistik_uc),
):
    """Dashboard için toplam ürün, kritik stok, günlük hareket ve toplam değer istatistikleri."""
    return uc.execute()
