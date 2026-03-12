from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role
from models import Kullanici
from services.marka_service import MarkaService
from schemas import MarkaCreate, MarkaUpdate, MarkaResponse

router = APIRouter(prefix="/api/markalar", tags=["Markalar"])


@router.get("/", response_model=list[MarkaResponse])
def markalari_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return MarkaService.get_markalar(db, skip=skip, limit=limit)


@router.get("/{marka_id}", response_model=MarkaResponse)
def marka_detay(
    marka_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return MarkaService.get_marka(db, marka_id)


@router.post("/", response_model=MarkaResponse, status_code=201)
def marka_ekle(
    marka: MarkaCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return MarkaService.create_marka(db, marka)


@router.put("/{marka_id}", response_model=MarkaResponse)
def marka_guncelle(
    marka_id: int,
    marka: MarkaUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return MarkaService.update_marka(db, marka_id, marka)


@router.delete("/{marka_id}")
def marka_sil(
    marka_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    MarkaService.delete_marka(db, marka_id)
    return {"success": True, "message": "Marka başarıyla pasife alındı", "id": marka_id}
