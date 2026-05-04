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

    def aktif_urun_idleri(self) -> list[int]:
        rows = (
            self._db.query(Urun.id)
            .filter(Urun.aktif.is_(True))
            .order_by(Urun.id.asc())
            .all()
        )
        return [row[0] for row in rows]

    def kategori_gunluk_medyan(self, kategori_id: int) -> Optional[float]:
        return self._gunluk_medyan_hesapla(Urun.kategori_id == kategori_id)

    def marka_gunluk_medyan(self, marka_id: int) -> Optional[float]:
        return self._gunluk_medyan_hesapla(Urun.marka_id == marka_id)

    def _gunluk_medyan_hesapla(self, urun_filter) -> Optional[float]:
        """Belirtilen urun grubunun son 90 gun gunluk toplam cikis ortalamasi.

        Saf medyan MySQL'de pahali; bunun yerine 'aktif gun ortalamasi'
        proxy'sini doneriz: toplam cikis / aktif gun sayisi (90 gun ufkunda).
        """
        bitis_dt = datetime.combine(date.today() + timedelta(days=1), time.min)
        baslangic_dt = bitis_dt - timedelta(days=90)

        urun_id_subq = (
            self._db.query(Urun.id)
            .filter(Urun.aktif.is_(True), urun_filter)
            .subquery()
        )

        gun = func.date(StokHareketi.tarih)
        toplam_cikis = self._db.query(
            func.coalesce(func.sum(StokHareketi.miktar), 0),
            func.count(func.distinct(gun)),
        ).filter(
            StokHareketi.urun_id.in_(self._db.query(urun_id_subq.c.id)),
            StokHareketi.hareket_tipi == "cikis",
            StokHareketi.tarih >= baslangic_dt,
            StokHareketi.tarih < bitis_dt,
        ).first()

        if not toplam_cikis or not toplam_cikis[1]:
            return None

        toplam, aktif_gun = toplam_cikis
        if aktif_gun == 0:
            return None
        return float(toplam) / float(aktif_gun)

    @staticmethod
    def _urun_kaydi(urun) -> TalepTahminUrunKaydi:
        return TalepTahminUrunKaydi(
            id=urun.id,
            isim=urun.isim,
            barkod=urun.barkod,
            min_stok=urun.min_stok or 0,
            stok_miktari=int(urun.stok_miktari or 0),
            kategori_id=urun.kategori_id,
            marka_id=urun.marka_id,
        )

    @staticmethod
    def _date_degeri(value) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
