from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Kullanici
from auth import get_current_user, require_role
from schemas import SistemLogResponse, SistemLogCreate
from services.sistem_log_service import SistemLogService

router = APIRouter(prefix="/api/sistem-loglari", tags=["Sistem Logları"])


@router.get("/", response_model=list[SistemLogResponse])
def get_loglar(
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Sistem loglarını getirir (sadece admin)."""
    return SistemLogService.get_loglar(db, limit=limit)


@router.post("/", response_model=SistemLogResponse)
def create_log(
    data: SistemLogCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Frontend'den doğrudan log kaydetmek için."""
    return SistemLogService.create_log(db, data, current_user)
