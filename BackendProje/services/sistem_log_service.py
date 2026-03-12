"""Sistem Logları — Service Layer"""
from sqlalchemy.orm import Session

from models import SistemLog, Kullanici
from schemas import SistemLogCreate, SistemLogResponse


class SistemLogService:

    @staticmethod
    def get_loglar(db: Session, limit: int = 100):
        """Son N sistem logu; kullanici_ad_soyad alanı ile birlikte döner."""
        loglar = (
            db.query(SistemLog)
            .order_by(SistemLog.tarih.desc())
            .limit(limit)
            .all()
        )
        return [
            SistemLogResponse(
                id=log.id,
                kullanici_id=log.kullanici_id,
                islem_tipi=log.islem_tipi,
                modul=log.modul,
                detay=log.detay,
                eski_veri=log.eski_veri,
                yeni_veri=log.yeni_veri,
                tarih=log.tarih,
                kullanici_ad_soyad=log.kullanici.ad_soyad if log.kullanici else "Bilinmeyen",
            )
            for log in loglar
        ]

    @staticmethod
    def create_log(db: Session, data: SistemLogCreate, current_user: Kullanici) -> SistemLogResponse:
        yeni_log = SistemLog(
            kullanici_id=current_user.id,
            islem_tipi=data.islem_tipi,
            modul=data.modul,
            detay=data.detay,
            eski_veri=data.eski_veri,
            yeni_veri=data.yeni_veri,
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
            kullanici_ad_soyad=current_user.ad_soyad,
        )
