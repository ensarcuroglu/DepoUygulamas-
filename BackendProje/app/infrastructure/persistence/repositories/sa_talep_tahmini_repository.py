from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.repositories.talep_tahmini_repository import (
    GunlukCikisKaydi,
    ITalepTahminiRepository,
    TalepTahminUrunKaydi,
)
from models import StokHareketi, Urun


class SqlAlchemyTalepTahminiRepository(ITalepTahminiRepository):
    def __init__(self, db: Session):
        self._db = db

    def urunleri_listele(
        self,
        limit: int = 100,
        search: Optional[str] = None,
    ) -> list[TalepTahminUrunKaydi]:
        query = self._db.query(Urun).filter(Urun.aktif.is_(True))

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Urun.isim.ilike(pattern),
                    Urun.barkod.ilike(pattern),
                    Urun.ean.ilike(pattern),
                )
            )

        urunler = query.order_by(Urun.isim.asc()).limit(limit).all()
        return [self._urun_kaydi(urun) for urun in urunler]

    def urun_getir(self, urun_id: int) -> Optional[TalepTahminUrunKaydi]:
        urun = (
            self._db.query(Urun)
            .filter(Urun.id == urun_id, Urun.aktif.is_(True))
            .first()
        )
        return self._urun_kaydi(urun) if urun else None

    def gunluk_cikislari_getir(
        self,
        urun_id: int,
        baslangic: date,
        bitis: date,
    ) -> list[GunlukCikisKaydi]:
        gun = func.date(StokHareketi.tarih).label("gun")
        baslangic_dt = datetime.combine(baslangic, time.min)
        bitis_dt = datetime.combine(bitis + timedelta(days=1), time.min)

        rows = (
            self._db.query(gun, func.coalesce(func.sum(StokHareketi.miktar), 0))
            .filter(
                StokHareketi.urun_id == urun_id,
                StokHareketi.hareket_tipi == "cikis",
                StokHareketi.tarih >= baslangic_dt,
                StokHareketi.tarih < bitis_dt,
            )
            .group_by(gun)
            .order_by(gun.asc())
            .all()
        )

        return [
            GunlukCikisKaydi(
                tarih=self._date_degeri(gun_degeri),
                miktar=float(miktar or 0),
            )
            for gun_degeri, miktar in rows
        ]

    @staticmethod
    def _urun_kaydi(urun: Urun) -> TalepTahminUrunKaydi:
        return TalepTahminUrunKaydi(
            id=urun.id,
            isim=urun.isim,
            barkod=urun.barkod,
            min_stok=urun.min_stok or 0,
            stok_miktari=int(urun.stok_miktari or 0),
        )

    @staticmethod
    def _date_degeri(value) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
