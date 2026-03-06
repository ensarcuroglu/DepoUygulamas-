from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from auth import get_current_user, require_role
from models import Kullanici
import crud
from schemas import (
    UrunCreate, UrunUpdate, UrunResponse, UrunListResponse
)

router = APIRouter(prefix="/api/urunler", tags=["Ürünler"])


@router.get("/", response_model=list[UrunListResponse])
def urunleri_listele(
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = Query(None, description="İsim, barkod, EAN veya açıklama ile ara"),
    kategori_id: Optional[int] = Query(None, description="Kategoriye göre filtrele"),
    marka_id: Optional[int] = Query(None, description="Markaya göre filtrele"),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Tüm ürünleri listeler. Arama, kategori ve marka filtresi destekler."""
    return crud.get_urunler(db, skip=skip, limit=limit, search=search,
                            kategori_id=kategori_id, marka_id=marka_id)


@router.get("/kritik", response_model=list[UrunListResponse])
def kritik_urunleri_getir(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Min stok seviyesinin altındaki ürünleri getirir."""
    return crud.get_kritik_urunler(db)


@router.get("/barkod/{barkod_kodu}", response_model=UrunResponse)
def urun_getir_by_barkod(
    barkod_kodu: str,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Barkod veya EAN numarasına göre tek bir ürün getirir"""
    db_urun = crud.get_urun_by_barkod(db, barkod=barkod_kodu)
    if not db_urun:
        raise HTTPException(status_code=404, detail="Bu barkoda ait ürün bulunamadı")
    return db_urun

@router.get("/{urun_id}", response_model=UrunResponse)
def urun_detay(
    urun_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Belirli bir ürünün tüm detaylarını getirir."""
    db_urun = crud.get_urun(db, urun_id)
    if not db_urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return db_urun


@router.post("/", response_model=UrunResponse, status_code=201)
def urun_ekle(
    urun: UrunCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni bir ürün ekler. Sadece admin."""
    return crud.create_urun(db, urun)


@router.put("/{urun_id}", response_model=UrunResponse)
def urun_guncelle(
    urun_id: int,
    urun: UrunUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Mevcut bir ürünü günceller. Sadece admin."""
    db_urun = crud.update_urun(db, urun_id, urun)
    if not db_urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return db_urun


@router.delete("/{urun_id}")
def urun_sil(
    urun_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Bir ürünü pasife alır (soft delete). Sadece admin."""
    success = crud.delete_urun(db, urun_id)
    if not success:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")
    return {"message": "Ürün başarıyla pasife alındı", "id": urun_id}
