from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role
from models import Kullanici
from services.kategori_service import KategoriService
from schemas import KategoriCreate, KategoriUpdate, KategoriResponse

router = APIRouter(prefix="/api/kategoriler", tags=["Kategoriler"])


@router.get("/", response_model=list[KategoriResponse])
def kategorileri_listele(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return KategoriService.get_kategoriler(db, skip=skip, limit=limit)


@router.get("/{kategori_id}", response_model=KategoriResponse)
def kategori_detay(
    kategori_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return KategoriService.get_kategori(db, kategori_id)


@router.post("/", response_model=KategoriResponse, status_code=201)
def kategori_ekle(
    kategori: KategoriCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return KategoriService.create_kategori(db, kategori, kullanici_id=current_user.id)


@router.put("/{kategori_id}", response_model=KategoriResponse)
def kategori_guncelle(
    kategori_id: int,
    kategori: KategoriUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    return KategoriService.update_kategori(db, kategori_id, kategori, kullanici_id=current_user.id)


@router.delete("/{kategori_id}")
def kategori_sil(
    kategori_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin")),
):
    KategoriService.delete_kategori(db, kategori_id, kullanici_id=current_user.id)
    return {"success": True, "message": "Kategori başarıyla pasife alındı", "id": kategori_id}
