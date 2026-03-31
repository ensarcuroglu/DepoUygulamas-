from datetime import datetime, timedelta

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

        bugun = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        yedi_gun_once = bugun - timedelta(days=6)

        bugunku_hareket = self._db.query(func.count(StokHareketi.id)).filter(
            StokHareketi.tarih >= bugun
        ).scalar()

        # Son 7 günlük stok hareketlerini çek ve Python'da grupla (veritabanı bağımsız gruplama)
        son_7_gun_hareketleri = self._db.query(
            StokHareketi.tarih,
            StokHareketi.hareket_tipi,
            StokHareketi.miktar
        ).filter(StokHareketi.tarih >= yedi_gun_once).all()

        akisi_dict = {}
        ay_isimleri = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
        
        for i in range(7):
            dt = bugun - timedelta(days=6 - i)  # Bugünden geriye 6 gün -> toplam 7 gün (artan sıra)
            day_str = f"{dt.day:02d} {ay_isimleri[dt.month - 1]}"
            akisi_dict[dt.date()] = {"day": day_str, "giris": 0, "cikis": 0}

        for h in son_7_gun_hareketleri:
            h_date = h.tarih.date()
            if h_date in akisi_dict:
                if h.hareket_tipi == "giris":
                    akisi_dict[h_date]["giris"] += h.miktar
                elif h.hareket_tipi == "cikis":
                    akisi_dict[h_date]["cikis"] += h.miktar

        return DashboardIstatistik(
            toplam_urun=urun_stats[0],
            kritik_stok_sayisi=urun_stats[1],
            bugunku_hareket=bugunku_hareket,
            toplam_deger=round(urun_stats[2], 2),
            stok_akisi=list(akisi_dict.values())
        )
