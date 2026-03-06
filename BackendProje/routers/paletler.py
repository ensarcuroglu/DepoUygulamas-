from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import get_current_user, require_role
from models import Kullanici
import crud
from schemas import PaletCreate, PaletUpdate, PaletResponse, PaletDetailResponse

router = APIRouter(prefix="/api/paletler", tags=["Paletler"])


@router.get("/", response_model=list[PaletDetailResponse])
def paletleri_listele(
    skip: int = 0,
    limit: int = 50,
    lot_id: Optional[int] = Query(None, description="LOT'a göre filtrele"),
    raf_id: Optional[int] = Query(None, description="Rafa göre filtrele"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Paletleri listeler. LOT veya raf bazlı filtreleme destekler."""
    return crud.get_paletler(db, skip=skip, limit=limit, lot_id=lot_id, raf_id=raf_id)


@router.get("/sonraki-numara")
def sonraki_palet_numarasi(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Bir sonraki palet barkod numarasını döner."""
    return {"palet_no": crud.get_sonraki_palet_no(db)}


@router.get("/barkod/{palet_no}", response_model=PaletDetailResponse)
def palet_getir_by_barkod(
    palet_no: str,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Palet barkod numarasına göre palet getirir."""
    db_palet = crud.get_palet_by_no(db, palet_no=palet_no)
    if not db_palet:
        raise HTTPException(status_code=404, detail="Bu numaraya ait palet bulunamadı")
    return db_palet


@router.get("/{palet_id}", response_model=PaletDetailResponse)
def palet_detay(
    palet_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Belirli bir paletin detaylarını getirir."""
    db_palet = crud.get_palet(db, palet_id)
    if not db_palet:
        raise HTTPException(status_code=404, detail="Palet bulunamadı")
    return db_palet


@router.post("/", response_model=PaletResponse, status_code=201)
def palet_ekle(
    palet: PaletCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni bir palet kaydı oluşturur. Sadece admin."""
    # LOT var mı kontrol et
    db_lot = crud.get_lot(db, palet.lot_id)
    if not db_lot:
        raise HTTPException(status_code=404, detail="LOT bulunamadı")

    # Raf belirtilmişse var mı kontrol et
    if palet.raf_id:
        db_raf = crud.get_raf(db, palet.raf_id)
        if not db_raf:
            raise HTTPException(status_code=404, detail="Raf bulunamadı")

    return crud.create_palet(db, palet)


@router.put("/{palet_id}", response_model=PaletResponse)
def palet_guncelle(
    palet_id: int,
    palet: PaletUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Mevcut bir paleti günceller. Sadece admin."""
    db_palet = crud.update_palet(db, palet_id, palet)
    if not db_palet:
        raise HTTPException(status_code=404, detail="Palet bulunamadı")
    return db_palet


@router.delete("/{palet_id}")
def palet_sil(
    palet_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Bir paleti pasife alır. Sadece admin."""
    success = crud.delete_palet(db, palet_id)
    if not success:
        raise HTTPException(status_code=404, detail="Palet bulunamadı")
    return {"message": "Palet başarıyla pasife alındı", "id": palet_id}
