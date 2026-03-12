from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import get_current_user
from models import Kullanici
from services.stok_service import StokService
from schemas import StokHareketiCreate, StokHareketiResponse
from limiter import limiter

router = APIRouter(prefix="/api/stok-hareketleri", tags=["Stok Hareketleri"])


@router.get("/", response_model=list[StokHareketiResponse])
@limiter.limit("100/minute")
def hareketleri_listele(
    request: Request,
    skip: int = 0,
    limit: int = 50,
    urun_id: Optional[int] = Query(None, description="Belirli ürüne göre filtrele"),
    lot_id: Optional[int] = Query(None, description="Belirli LOT'a göre filtrele"),
    hareket_tipi: Optional[str] = Query(None, description="'giris' veya 'cikis' olarak filtrele"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """Stok hareketlerini listeler. Ürün, LOT veya hareket tipine göre filtreleme destekler."""
    return StokService.get_hareketler(
        db, skip=skip, limit=limit,
        urun_id=urun_id, lot_id=lot_id, hareket_tipi=hareket_tipi,
    )


@router.post("/", response_model=StokHareketiResponse, status_code=201)
@limiter.limit("50/minute")
def hareket_ekle(
    request: Request,
    hareket: StokHareketiCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user),
):
    """
    Yeni stok hareketi oluşturur.
    - hareket_tipi: 'giris' veya 'cikis'
    - Çıkışta palet belirtilmişse otomatik olarak paleti pasife alır
    - Hareketi gerçekleştiren kullanıcı otomatik kaydedilir
    """
    return StokService.create_hareket(db, hareket, kullanici_id=current_user.id)
