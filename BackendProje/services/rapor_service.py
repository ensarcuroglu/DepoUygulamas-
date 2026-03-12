"""Rapor — Service Layer"""
from typing import Optional
from datetime import date, datetime
from sqlalchemy.orm import Session

import crud
from schemas import (
    RaporSablonuCreate, RaporSablonuUpdate,
    RaporLoguCreate,
    RaporScheduleCreate, RaporScheduleUpdate,
)
from core.exceptions import NotFoundError, BadRequestError


class RaporService:

    # ── Şablonlar ──────────────────────────────────────────────────────

    @staticmethod
    def get_sablonlar(db: Session, skip: int = 0, limit: int = 100, tur: Optional[str] = None):
        return crud.get_rapor_sablonlari(db, skip=skip, limit=limit, tur=tur)

    @staticmethod
    def get_sablon(db: Session, sablon_id: int):
        sablon = crud.get_rapor_sablonu(db, sablon_id)
        if not sablon:
            raise NotFoundError("Rapor şablonu", sablon_id)
        return sablon

    @staticmethod
    def create_sablon(db: Session, sablon: RaporSablonuCreate, kullanici_id: int):
        return crud.create_rapor_sablonu(db, sablon, kullanici_id=kullanici_id)

    @staticmethod
    def update_sablon(db: Session, sablon_id: int, sablon_update: RaporSablonuUpdate, kullanici_id: int):
        sablon = crud.update_rapor_sablonu(db, sablon_id, sablon_update, kullanici_id=kullanici_id)
        if not sablon:
            raise NotFoundError("Rapor şablonu", sablon_id)
        return sablon

    @staticmethod
    def delete_sablon(db: Session, sablon_id: int, kullanici_id: int):
        success = crud.delete_rapor_sablonu(db, sablon_id, kullanici_id=kullanici_id)
        if not success:
            raise NotFoundError("Rapor şablonu", sablon_id)

    # ── Veri Endpointleri ──────────────────────────────────────────────

    @staticmethod
    def get_stok_verisi(db: Session, urun_id: Optional[int] = None):
        return crud.get_stok_raporu_verileri(db, urun_id=urun_id)

    @staticmethod
    def get_siparis_verisi(
        db: Session,
        baslang_tarihi: Optional[date] = None,
        bitis_tarihi: Optional[date] = None,
    ):
        return crud.get_siparis_raporu_verileri(db, baslang_tarihi, bitis_tarihi)

    @staticmethod
    def get_hareket_verisi(
        db: Session,
        baslang_tarihi: Optional[date] = None,
        bitis_tarihi: Optional[date] = None,
    ):
        return crud.get_hareket_raporu_verileri(db, baslang_tarihi, bitis_tarihi)

    @staticmethod
    def get_kritik_stok(db: Session):
        rows = crud.get_kritik_stok_raporu(db)
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def get_skt(db: Session, gun: int = 30):
        rows = crud.get_skt_raporu(db, gun=gun)
        return [dict(r._mapping) for r in rows]

    @staticmethod
    def get_abc_analiz(db: Session):
        return crud.get_abc_analiz(db)

    @staticmethod
    def get_doluluk(db: Session):
        return crud.get_depo_doluluk(db)

    @staticmethod
    def get_export_data(
        db: Session,
        tur: str,
        baslang_tarihi: Optional[date] = None,
        bitis_tarihi: Optional[date] = None,
    ):
        """Export için ham veri satırlarını döner. Geçersiz tur → BadRequestError."""
        if tur == "stok":
            return crud.get_stok_raporu_verileri(db)
        elif tur == "siparis":
            return crud.get_siparis_raporu_verileri(db, baslang_tarihi, bitis_tarihi)
        elif tur == "hareket":
            return crud.get_hareket_raporu_verileri(db, baslang_tarihi, bitis_tarihi)
        elif tur == "kritik_stok":
            return crud.get_kritik_stok_raporu(db)
        elif tur == "skt":
            return crud.get_skt_raporu(db)
        else:
            raise BadRequestError(f"Geçersiz rapor türü: {tur}")

    # ── Log Yardımcısı ─────────────────────────────────────────────────

    @staticmethod
    def log_yaz(
        db: Session,
        parametreler: dict,
        durum: str,
        kullanici_id: int,
        sablon_id: Optional[int] = None,
    ):
        return crud.create_rapor_logu(
            db,
            RaporLoguCreate(sablon_id=sablon_id, parametreler=parametreler, durum=durum),
            kullanici_id=kullanici_id,
        )

    # ── Loglar ─────────────────────────────────────────────────────────

    @staticmethod
    def get_loglar(db: Session, skip: int = 0, limit: int = 100, sablon_id: Optional[int] = None):
        return crud.get_rapor_loglari(db, skip=skip, limit=limit, sablon_id=sablon_id)

    # ── Schedule ───────────────────────────────────────────────────────

    @staticmethod
    def get_schedules(db: Session, skip: int = 0, limit: int = 100):
        return crud.get_rapor_schedules(db, skip=skip, limit=limit)

    @staticmethod
    def get_schedule(db: Session, schedule_id: int):
        schedule = crud.get_rapor_schedule(db, schedule_id)
        if not schedule:
            raise NotFoundError("Zamanlı rapor", schedule_id)
        return schedule

    @staticmethod
    def create_schedule(db: Session, schedule: RaporScheduleCreate, kullanici_id: int):
        return crud.create_rapor_schedule(db, schedule, kullanici_id=kullanici_id)

    @staticmethod
    def update_schedule(
        db: Session,
        schedule_id: int,
        schedule_update: RaporScheduleUpdate,
        kullanici_id: int,
    ):
        schedule = crud.update_rapor_schedule(db, schedule_id, schedule_update, kullanici_id=kullanici_id)
        if not schedule:
            raise NotFoundError("Zamanlı rapor", schedule_id)
        return schedule

    @staticmethod
    def delete_schedule(db: Session, schedule_id: int, kullanici_id: int):
        success = crud.delete_rapor_schedule(db, schedule_id, kullanici_id=kullanici_id)
        if not success:
            raise NotFoundError("Zamanlı rapor", schedule_id)

    @staticmethod
    def tetikle_schedule(db: Session, schedule_id: int, kullanici_id: int) -> dict:
        """Zamanlı raporu manuel tetikler, log yazar ve özet döner."""
        schedule = RaporService.get_schedule(db, schedule_id)  # raises NotFoundError if missing

        schedule.son_calistirilma = datetime.utcnow()
        db.commit()

        RaporService.log_yaz(
            db,
            parametreler={
                "periyod": schedule.periyod,
                "format": schedule.format,
                "tetikleyen": "manuel",
            },
            durum="Basarili",
            kullanici_id=kullanici_id,
            sablon_id=schedule.sablon_id,
        )

        return {
            "message": f"'{schedule.sablon_adi}' raporu tetiklendi",
            "schedule_id": schedule_id,
            "son_calistirilma": schedule.son_calistirilma,
        }
