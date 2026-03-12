from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import get_current_user, require_role
from models import Kullanici
from services.palet_service import PaletService
from core.exceptions import NotFoundError
from schemas import PaletCreate, PaletUpdate, PaletResponse, PaletDetailResponse

router = APIRouter(prefix="/api/paletler", tags=["Paletler"])


@router.get("/", response_model=list[PaletDetailResponse])
def paletleri_listele(
    skip: int = 0,
    limit: int = 50,
    lot_id: Optional[int] = Query(None, description="LOT'a göre filtrele"),
    raf_id: Optional[int] = Query(None, description="Rafa göre filtrele"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Paletleri listeler. LOT veya raf bazlı filtreleme destekler."""
    return PaletService.get_paletler(db, skip=skip, limit=limit, lot_id=lot_id, raf_id=raf_id)


@router.get("/sonraki-numara")
def sonraki_palet_numarasi(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Bir sonraki palet barkod numarasını döner."""
    return {"palet_no": PaletService.get_sonraki_palet_no(db)}


@router.get("/barkod/{palet_no}", response_model=PaletDetailResponse)
def palet_getir_by_barkod(
    palet_no: str,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Palet barkod numarasına göre palet getirir."""
    palet = PaletService.get_palet_by_no(db, palet_no)
    if not palet:
        raise NotFoundError("Palet barkodu", palet_no)
    return palet


@router.get("/{palet_id}", response_model=PaletDetailResponse)
def palet_detay(
    palet_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Belirli bir paletin detaylarını getirir."""
    return PaletService.get_palet(db, palet_id)


@router.post("/", response_model=PaletResponse, status_code=201)
def palet_ekle(
    palet: PaletCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Yeni bir palet kaydı oluşturur. Sadece admin."""
    return PaletService.create_palet(db, palet)


@router.put("/{palet_id}", response_model=PaletResponse)
def palet_guncelle(
    palet_id: int,
    palet: PaletUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Mevcut bir paleti günceller. Sadece admin."""
    return PaletService.update_palet(db, palet_id, palet)


@router.delete("/{palet_id}")
def palet_sil(
    palet_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    """Bir paleti pasife alır. Sadece admin."""
    PaletService.delete_palet(db, palet_id)
    return {"success": True, "message": "Palet başarıyla pasife alındı", "id": palet_id}
