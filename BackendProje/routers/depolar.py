from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role
from models import Kullanici
from services.depo_service import DepoService
from schemas import DepoCreate, DepoUpdate, DepoResponse

router = APIRouter(
    prefix="/api/depolar",
    tags=["Depolar"],
    dependencies=[Depends(require_role("admin", "lojistik"))],
)


@router.get("/", response_model=list[DepoResponse])
def depolari_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return DepoService.get_depolar(db, skip=skip, limit=limit)


@router.get("/{depo_id}", response_model=DepoResponse)
def depo_detay(
    depo_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return DepoService.get_depo(db, depo_id)


@router.post("/", response_model=DepoResponse, status_code=201)
def depo_ekle(
    depo: DepoCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return DepoService.create_depo(db, depo, kullanici_id=current_user.id)


@router.put("/{depo_id}", response_model=DepoResponse)
def depo_guncelle(
    depo_id: int,
    depo: DepoUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    return DepoService.update_depo(db, depo_id, depo)


@router.delete("/{depo_id}")
def depo_sil(
    depo_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik")),
):
    DepoService.delete_depo(db, depo_id)
    return {"success": True, "message": "Depo başarıyla pasife alındı", "id": depo_id}
