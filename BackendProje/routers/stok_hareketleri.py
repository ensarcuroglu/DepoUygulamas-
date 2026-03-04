from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import get_current_user
from models import Kullanici
import crud
from schemas import StokHareketiCreate, StokHareketiResponse

router = APIRouter(prefix="/api/stok-hareketleri", tags=["Stok Hareketleri"])


@router.get("/", response_model=list[StokHareketiResponse])
def hareketleri_listele(
    skip: int = 0,
    limit: int = 50,
    urun_id: Optional[int] = Query(None, description="Belirli ürüne göre filtrele"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Stok hareketlerini listeler. Ürüne göre filtreleme destekler."""
    return crud.get_stok_hareketleri(db, skip=skip, limit=limit, urun_id=urun_id)


@router.post("/", response_model=StokHareketiResponse, status_code=201)
def hareket_ekle(
    hareket: StokHareketiCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Yeni stok hareketi oluşturur.
    - hareket_tipi: "giris" veya "cikis"
    - Otomatik olarak ürünün stok miktarını günceller
    - Hareketi gerçekleştiren kullanıcı otomatik kaydedilir
    """
    if hareket.hareket_tipi not in ("giris", "cikis"):
        raise HTTPException(
            status_code=400,
            detail="Hareket tipi 'giris' veya 'cikis' olmalıdır"
        )

    if hareket.miktar <= 0:
        raise HTTPException(
            status_code=400,
            detail="Miktar 0'dan büyük olmalıdır"
        )

    # Ürünün varlığını kontrol et
    db_urun = crud.get_urun(db, hareket.urun_id)
    if not db_urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    # Çıkış yapılıyorsa yeterli stok var mı kontrol et
    if hareket.hareket_tipi == "cikis" and db_urun.stok_miktari < hareket.miktar:
        raise HTTPException(
            status_code=400,
            detail=f"Yetersiz stok. Mevcut: {db_urun.stok_miktari}, Talep: {hareket.miktar}"
        )

    # Kullanıcı ID'sini otomatik olarak kaydet
    return crud.create_stok_hareketi(db, hareket, kullanici_id=current_user.id)
