from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import Kullanici, SistemLog
from auth import get_current_user
from schemas import SistemLogResponse, SistemLogCreate

router = APIRouter(prefix="/api/sistem-loglari", tags=["Sistem Logları"])

def require_admin(current_user: Kullanici = Depends(get_current_user)) -> Kullanici:
    if current_user.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu işlemi yapmak için yetkiniz yok."
        )
    return current_user

@router.get("/", response_model=list[SistemLogResponse])
def get_loglar(
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(require_admin),
    limit: int = 100
):
    """
    Sistem loglarını getirir (sadece admin)
    """
    loglar = db.query(SistemLog).order_by(SistemLog.tarih.desc()).limit(limit).all()
    
    # Kullanıcı ad soyadını manuel mapleme
    sonuclar = []
    for log in loglar:
        ad_soyad = "Bilinmeyen"
        if log.kullanici:
            ad_soyad = log.kullanici.ad_soyad
        
        son_log = SistemLogResponse(
            id=log.id,
            kullanici_id=log.kullanici_id,
            islem_tipi=log.islem_tipi,
            modul=log.modul,
            detay=log.detay,
            eski_veri=log.eski_veri,
            yeni_veri=log.yeni_veri,
            tarih=log.tarih,
            kullanici_ad_soyad=ad_soyad
        )
        sonuclar.append(son_log)
        
    return sonuclar

@router.post("/", response_model=SistemLogResponse)
def create_log(
    data: SistemLogCreate,
    db: Session = Depends(get_db),
    current_user: Kullanici = Depends(get_current_user)
):
    """
    Frontend'den doğrudan log kaydetmek için (isteğe bağlı kullanım)
    """
    yeni_log = SistemLog(
        kullanici_id=current_user.id,
        islem_tipi=data.islem_tipi,
        modul=data.modul,
        detay=data.detay,
        eski_veri=data.eski_veri,
        yeni_veri=data.yeni_veri
    )
    db.add(yeni_log)
    db.commit()
    db.refresh(yeni_log)
    
    return SistemLogResponse(
        id=yeni_log.id,
        kullanici_id=yeni_log.kullanici_id,
        islem_tipi=yeni_log.islem_tipi,
        modul=yeni_log.modul,
        detay=yeni_log.detay,
        eski_veri=yeni_log.eski_veri,
        yeni_veri=yeni_log.yeni_veri,
        tarih=yeni_log.tarih,
        kullanici_ad_soyad=current_user.ad_soyad
    )
