from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role
from models import Kullanici
import crud
from schemas import KategoriCreate, KategoriUpdate, KategoriResponse

router = APIRouter(prefix="/api/kategoriler", tags=["Kategoriler"])

# Tüm endpoint'ler sadece admin erişimlidir
_admin = Depends(require_role("admin"))


@router.get("/", response_model=list[KategoriResponse])
def kategorileri_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Tüm kategorileri listeler."""
    return crud.get_kategoriler(db, skip=skip, limit=limit)


@router.get("/{kategori_id}", response_model=KategoriResponse)
def kategori_detay(
    kategori_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Belirli bir kategorinin detaylarını getirir."""
    db_kategori = crud.get_kategori(db, kategori_id)
    if not db_kategori:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    return db_kategori


@router.post("/", response_model=KategoriResponse, status_code=201)
def kategori_ekle(
    kategori: KategoriCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni bir kategori ekler."""
    return crud.create_kategori(db, kategori)


@router.put("/{kategori_id}", response_model=KategoriResponse)
def kategori_guncelle(
    kategori_id: int,
    kategori: KategoriUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Mevcut bir kategoriyi günceller."""
    db_kategori = crud.update_kategori(db, kategori_id, kategori)
    if not db_kategori:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    return db_kategori


@router.delete("/{kategori_id}")
def kategori_sil(
    kategori_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Bir kategoriyi pasife alır (soft delete)."""
    success = crud.delete_kategori(db, kategori_id)
    if not success:
        raise HTTPException(status_code=404, detail="Kategori bulunamadı")
    return {"message": "Kategori başarıyla pasife alındı", "id": kategori_id}
