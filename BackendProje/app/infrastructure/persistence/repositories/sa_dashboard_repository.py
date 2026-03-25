from datetime import datetime

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from app.core.repositories.dashboard_repository import IDashboardRepository, DashboardIstatistik
from models import Urun, StokHareketi


class SqlAlchemyDashboardRepository(IDashboardRepository):

    def __init__(self, db: Session):
        self._db = db

    def istatistik_getir(self) -> DashboardIstatistik:
        # Tek sorguda 3 Urun aggregate'i (toplam, kritik stok, envanter değeri)
        urun_stats = self._db.query(
            func.count(Urun.id),
            func.count(case((Urun.stok_miktari <= Urun.min_stok, 1))),
            func.coalesce(func.sum(Urun.stok_miktari * Urun.fiyat), 0.0),
        ).filter(Urun.aktif == True).one()

        bugun = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        bugunku_hareket = self._db.query(func.count(StokHareketi.id)).filter(
            StokHareketi.tarih >= bugun
        ).scalar()

        return DashboardIstatistik(
            toplam_urun=urun_stats[0],
            kritik_stok_sayisi=urun_stats[1],
            bugunku_hareket=bugunku_hareket,
            toplam_deger=round(urun_stats[2], 2),
        )
