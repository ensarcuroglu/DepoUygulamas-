from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from models import Urun, StokHareketi


def get_dashboard_stats(db: Session):
    toplam_urun = db.query(func.count(Urun.id)).filter(Urun.aktif == True).scalar()

    kritik_stok = db.query(func.count(Urun.id)).filter(
        Urun.aktif == True,
        Urun.stok_miktari <= Urun.min_stok
    ).scalar()

    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    bugunku_hareket = db.query(func.count(StokHareketi.id)).filter(
        StokHareketi.tarih >= bugun
    ).scalar()

    toplam_deger = db.query(func.coalesce(func.sum(Urun.stok_miktari * Urun.fiyat), 0.0)).filter(Urun.aktif == True).scalar()

    return {
        "toplam_urun": toplam_urun,
        "kritik_stok_sayisi": kritik_stok,
        "bugunku_hareket": bugunku_hareket,
        "toplam_deger": round(toplam_deger, 2)
    }
