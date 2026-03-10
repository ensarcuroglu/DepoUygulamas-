from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import Optional

from database import get_db
from auth import require_role
from models import Kullanici, Irsaliye, Siparis, SiparisKalemi, Urun
import crud
from schemas import (
    IrsaliyeCreate, IrsaliyeUpdate, IrsaliyeResponse
)

router = APIRouter(prefix="/api/irsaliyeler", tags=["İrsaliyeler"])


@router.get("/", response_model=list[IrsaliyeResponse])
def irsaliyeler_listele(
    skip: int = 0,
    limit: int = 100,
    durum: Optional[str] = Query(None),
    arama: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Tüm irsaliyeleri listeler (filtreleme ve arama destekli)."""
    return crud.get_irsaliyeler(db, skip=skip, limit=limit, durum=durum, arama=arama)


@router.get("/{irsaliye_id}", response_model=IrsaliyeResponse)
def irsaliye_detay(
    irsaliye_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """Belirli bir irsaliyenin detaylarını getirir."""
    db_irsaliye = crud.get_irsaliye(db, irsaliye_id)
    if not db_irsaliye:
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    return db_irsaliye


@router.post("/", response_model=IrsaliyeResponse, status_code=201)
def irsaliye_ekle(
    irsaliye: IrsaliyeCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Yeni bir irsaliye oluşturur (otomatik no üretimi)."""
    # Sipariş var mı kontrol et
    db_siparis = crud.get_siparis(db, irsaliye.siparis_id)
    if not db_siparis:
        raise HTTPException(status_code=404, detail="Sipariş bulunamadı")

    return crud.create_irsaliye(db, irsaliye, kullanici_id=current_user.id)


@router.put("/{irsaliye_id}", response_model=IrsaliyeResponse)
def irsaliye_guncelle(
    irsaliye_id: int,
    irsaliye_update: IrsaliyeUpdate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik"))
):
    """Mevcut bir irsaliyeyi günceller/durum değiştirir."""
    db_irsaliye = crud.update_irsaliye(db, irsaliye_id, irsaliye_update, kullanici_id=current_user.id)
    if not db_irsaliye:
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")
    return db_irsaliye


@router.get("/{irsaliye_id}/yazdir")
def irsaliye_yazdir_verisi(
    irsaliye_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin", "lojistik", "depocu"))
):
    """İrsaliye yazdırma verisi: irsaliye + sipariş + kalemler (ürün adıyla birlikte)"""
    db_irsaliye = db.query(Irsaliye).options(
        joinedload(Irsaliye.siparis).joinedload(Siparis.kalemler).joinedload(SiparisKalemi.urun)
    ).filter(Irsaliye.id == irsaliye_id).first()

    if not db_irsaliye:
        raise HTTPException(status_code=404, detail="İrsaliye bulunamadı")

    siparis = db_irsaliye.siparis
    kalemler = [
        {
            "urun_id": k.urun_id,
            "urun_isim": k.urun.isim if k.urun else "-",
            "miktar": k.miktar,
            "birim_fiyat": k.birim_fiyat,
            "kdv_orani": k.kdv_orani,
            "toplam": k.toplam
        }
        for k in (siparis.kalemler if siparis else [])
    ]

    return {
        "irsaliye": {
            "id": db_irsaliye.id,
            "irsaliye_no": db_irsaliye.irsaliye_no,
            "irsaliye_tarihi": str(db_irsaliye.irsaliye_tarihi),
            "belge_turu": db_irsaliye.belge_turu,
            "tir_plaka": db_irsaliye.tir_plaka,
            "sofor_adi": db_irsaliye.sofor_adi,
            "durum": db_irsaliye.durum,
        },
        "siparis": {
            "siparis_no": siparis.siparis_no if siparis else "-",
            "musteri_adi": siparis.musteri_adi if siparis else "-",
            "teslimat_adresi": siparis.teslimat_adresi if siparis else "-",
            "teslimat_tarihi": str(siparis.teslimat_tarihi) if siparis else "-",
            "top_tutar": siparis.top_tutar if siparis else 0,
            "top_miktar": siparis.top_miktar if siparis else 0,
        },
        "kalemler": kalemler
    }
