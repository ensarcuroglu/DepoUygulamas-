from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import List

from database import get_db
from models import StokSayim, StokSayimKalemi, Urun, Palet, Lot, Kullanici
from auth import get_current_user, require_role
from schemas import StokSayimRead, StokSayimKalemiRead, StokSayimCreate, StokSayimKalemiCreate

router = APIRouter(prefix="/api/stok-sayimlar", tags=["stok-sayim"])


# ========================
# SAYIMLARI LİSTELE
# ========================
@router.get("", response_model=List[StokSayimRead])
def sayimlari_listele(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """Tüm stok sayımlarını listeler."""
    sayimlar = db.query(StokSayim).filter(StokSayim.aktif == True).order_by(StokSayim.olusturma_tarihi.desc()).all()
    # urun_adi alanını doldur
    for sayim in sayimlar:
        for kalem in sayim.sayim_kalemleri:
            if kalem.urun:
                kalem.urun_adi = kalem.urun.adi
    return sayimlar


# ========================
# SAYIM DETAYI
# ========================
@router.get("/{sayim_id}", response_model=StokSayimRead)
def sayim_detayi(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
    if not sayim:
        raise HTTPException(status_code=404, detail="Sayım bulunamadı")
    for kalem in sayim.sayim_kalemleri:
        if kalem.urun:
            kalem.urun_adi = kalem.urun.adi
    return sayim


# ========================
# SAYIM BAŞLAT
# ========================
@router.post("", response_model=StokSayimRead)
def sayim_basla(
    sayim_data: StokSayimCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """Yeni stok sayımı oturumu başlatır; mevcut stok durumunu snapshot olarak kaydeder."""

    now = datetime.utcnow()
    sayim_no = f"SAY-{now.year}{now.month:02d}-{now.day:02d}-{now.hour:02d}{now.minute:02d}"

    # Aynı dakikada çakışma olmaması için sequence ekle
    mevcut = db.query(StokSayim).filter(StokSayim.sayim_no == sayim_no).first()
    if mevcut:
        sayim_no = f"{sayim_no}-{now.second:02d}"

    # Mevcut stok snapshot'ını al (Palet aggregation üzerinden)
    urunler = db.query(Urun).filter(Urun.aktif == True).all()
    referans_stok = {}
    for urun in urunler:
        toplam_koli = db.query(func.sum(Palet.koli_adedi)).filter(
            Palet.lot_id.in_(
                db.query(Lot.id).filter(Lot.urun_id == urun.id, Lot.aktif == True)
            ),
            Palet.aktif == True
        ).scalar() or 0
        referans_stok[str(urun.id)] = int(toplam_koli)

    yeni_sayim = StokSayim(
        sayim_no=sayim_no,
        aciklama=sayim_data.aciklama or "",
        kontrol_eden_user_id=current_user.id,
        referans_stok_json=referans_stok,
        durum="devam_ediyor"
    )

    db.add(yeni_sayim)
    db.commit()
    db.refresh(yeni_sayim)
    return yeni_sayim


# ========================
# ÜRÜN SAYIMI KAYDET
# ========================
@router.post("/{sayim_id}/kalemler", response_model=StokSayimKalemiRead)
def urun_sayisi_kaydet(
    sayim_id: int,
    kalem_data: StokSayimKalemiCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Belirli bir ürünün sayılan miktarını kaydet.
    Aynı ürün tekrar tarandığında miktar güncellenir (upsert).
    """
    sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
    if not sayim:
        raise HTTPException(status_code=404, detail="Sayım bulunamadı")
    if sayim.durum != "devam_ediyor":
        raise HTTPException(status_code=400, detail="Bu sayım aktif değil")

    urun = db.query(Urun).filter(Urun.id == kalem_data.urun_id).first()
    if not urun:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı")

    # Varsa güncelle, yoksa oluştur (upsert)
    kalem = db.query(StokSayimKalemi).filter(
        StokSayimKalemi.sayim_id == sayim_id,
        StokSayimKalemi.urun_id == kalem_data.urun_id
    ).first()

    if kalem:
        kalem.sayilan_miktar = kalem_data.sayilan_miktar
        kalem.notlar = kalem_data.notlar or ""
        kalem.sayim_tarihi = datetime.utcnow()
    else:
        kalem = StokSayimKalemi(
            sayim_id=sayim_id,
            urun_id=kalem_data.urun_id,
            sayilan_miktar=kalem_data.sayilan_miktar,
            notlar=kalem_data.notlar or "",
            user_id=current_user.id
        )
        db.add(kalem)

    db.commit()
    db.refresh(kalem)
    kalem.urun_adi = urun.adi
    return kalem


# ========================
# VARYANS RAPORU
# ========================
@router.get("/{sayim_id}/varyans")
def varyans_hesapla(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Sayım kapatılırken beklenen stok ile sayılan miktarı karşılaştırır.
    Sapmaları raporlar.
    """
    sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
    if not sayim:
        raise HTTPException(status_code=404, detail="Sayım bulunamadı")

    if not sayim.referans_stok_json:
        return {"sayim_no": sayim.sayim_no, "varyanslar": [], "toplam_sapma": 0, "sapma_orani": 0}

    varyanslar = []
    toplam_fark = 0

    for urun_id_str, beklenen_miktar in sayim.referans_stok_json.items():
        urun_id = int(urun_id_str)

        kalem = db.query(StokSayimKalemi).filter(
            StokSayimKalemi.sayim_id == sayim_id,
            StokSayimKalemi.urun_id == urun_id
        ).first()

        sayilan_miktar = kalem.sayilan_miktar if kalem else 0
        fark = sayilan_miktar - beklenen_miktar

        if abs(fark) > 0:
            urun = db.query(Urun).filter(Urun.id == urun_id).first()
            urun_adi = urun.adi if urun else f"Ürün #{urun_id}"
            varyanslar.append({
                "urun_id": urun_id,
                "urun_adi": urun_adi,
                "beklenen": beklenen_miktar,
                "sayilan": sayilan_miktar,
                "fark": fark,
                "yuzde": round(fark / beklenen_miktar * 100, 1) if beklenen_miktar > 0 else 0,
                "notlar": kalem.notlar if kalem else ""
            })
            toplam_fark += abs(fark)

    return {
        "sayim_no": sayim.sayim_no,
        "referans_tarih": sayim.baslangic_tarihi,
        "varyanslar": varyanslar,
        "toplam_sapma": toplam_fark,
        "sayilan_urun_sayisi": len(sayim.sayim_kalemleri),
        "sapma_orani": round(len(varyanslar) / len(sayim.referans_stok_json) * 100, 1) if sayim.referans_stok_json else 0
    }


# ========================
# SAYIMI KAPAT & ONAYLA
# ========================
@router.post("/{sayim_id}/onayla")
def sayimi_onayla(
    sayim_id: int,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_role("admin"))
):
    """
    Sayımı kapatır ve 'onaylandı' durumuna geçirir.
    """
    sayim = db.query(StokSayim).filter(StokSayim.id == sayim_id).first()
    if not sayim:
        raise HTTPException(status_code=404, detail="Sayım bulunamadı")
    if sayim.durum not in ("devam_ediyor", "oluşturuldu"):
        raise HTTPException(status_code=400, detail=f"Sayım zaten '{sayim.durum}' durumunda")

    sayim.durum = "onaylandı"
    sayim.bitis_tarihi = datetime.utcnow()
    sayim.onaylayan_user_id = current_user.id

    db.commit()
    return {"message": "Sayım onaylandı", "sayim_no": sayim.sayim_no}
