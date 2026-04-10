from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.entities.rapor import RaporSablonu, RaporLogu, RaporSchedule
from app.core.repositories.rapor_repository import (
    IRaporSablonuRepository, IRaporLoguRepository, IRaporScheduleRepository,
    IRaporVeriRepository,
)
from app.infrastructure.persistence.mappers import (
    rapor_sablonu_to_entity, rapor_sablonu_to_orm,
    rapor_logu_to_entity, rapor_logu_to_orm,
    rapor_schedule_to_entity, rapor_schedule_to_orm,
)
from models import (
    RaporSablonu as RaporSablonuORM,
    RaporLogu as RaporLoguORM,
    RaporSchedule as RaporScheduleORM,
    Urun, Marka, Kategori, Siparis, SiparisKalemi,
    StokHareketi, Kullanici, Lot, Palet, Raf,
)


# ════════════════════════════════════════════
# RAPOR ŞABLONU
# ════════════════════════════════════════════

class SqlAlchemyRaporSablonuRepository(IRaporSablonuRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        tur: Optional[str] = None, is_aktif: bool = True,
    ) -> List[RaporSablonu]:
        query = self._db.query(RaporSablonuORM)
        if is_aktif:
            query = query.filter(RaporSablonuORM.is_aktif)
        if tur:
            query = query.filter(RaporSablonuORM.tur == tur)
        orm_list = query.order_by(RaporSablonuORM.ad).offset(skip).limit(limit).all()
        return [rapor_sablonu_to_entity(o) for o in orm_list]

    def getir_id_ile(self, sablon_id: int) -> Optional[RaporSablonu]:
        orm = self._db.query(RaporSablonuORM).filter(RaporSablonuORM.id == sablon_id).first()
        return rapor_sablonu_to_entity(orm) if orm else None

    def olustur(self, sablon: RaporSablonu) -> RaporSablonu:
        orm = rapor_sablonu_to_orm(sablon)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return rapor_sablonu_to_entity(orm)

    def guncelle(self, sablon: RaporSablonu) -> RaporSablonu:
        orm = self._db.query(RaporSablonuORM).filter(RaporSablonuORM.id == sablon.id).first()
        if not orm:
            return None
        orm.ad = sablon.ad
        orm.tur = sablon.tur
        orm.aciklama = sablon.aciklama
        orm.config = sablon.config
        orm.is_aktif = sablon.is_aktif
        orm.guncelleme_tarihi = sablon.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return rapor_sablonu_to_entity(orm)

    def sil(self, sablon_id: int) -> bool:
        orm = self._db.query(RaporSablonuORM).filter(RaporSablonuORM.id == sablon_id).first()
        if not orm:
            return False
        orm.is_aktif = False
        self._db.commit()
        return True


# ════════════════════════════════════════════
# RAPOR LOGU
# ════════════════════════════════════════════

class SqlAlchemyRaporLoguRepository(IRaporLoguRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        sablon_id: Optional[int] = None,
    ) -> List[RaporLogu]:
        query = self._db.query(RaporLoguORM).options(
            joinedload(RaporLoguORM.sablon),
        )
        if sablon_id:
            query = query.filter(RaporLoguORM.sablon_id == sablon_id)
        orm_list = query.order_by(
            RaporLoguORM.olusturma_tarihi.desc()
        ).offset(skip).limit(limit).all()
        return [rapor_logu_to_entity(o) for o in orm_list]

    def olustur(self, log: RaporLogu) -> RaporLogu:
        orm = rapor_logu_to_orm(log)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return rapor_logu_to_entity(orm)


# ════════════════════════════════════════════
# RAPOR SCHEDULE
# ════════════════════════════════════════════

class SqlAlchemyRaporScheduleRepository(IRaporScheduleRepository):

    def __init__(self, db: Session):
        self._db = db

    def getir_hepsi(
        self, skip: int = 0, limit: int = 100,
        is_aktif: bool = True,
    ) -> List[RaporSchedule]:
        query = self._db.query(RaporScheduleORM).options(
            joinedload(RaporScheduleORM.sablon),
        )
        if is_aktif:
            query = query.filter(RaporScheduleORM.is_aktif)
        orm_list = query.order_by(
            RaporScheduleORM.sablon_adi
        ).offset(skip).limit(limit).all()
        return [rapor_schedule_to_entity(o) for o in orm_list]

    def getir_id_ile(self, schedule_id: int) -> Optional[RaporSchedule]:
        orm = self._db.query(RaporScheduleORM).options(
            joinedload(RaporScheduleORM.sablon),
        ).filter(RaporScheduleORM.id == schedule_id).first()
        return rapor_schedule_to_entity(orm) if orm else None

    def olustur(self, schedule: RaporSchedule) -> RaporSchedule:
        orm = rapor_schedule_to_orm(schedule)
        orm.id = None
        self._db.add(orm)
        self._db.commit()
        self._db.refresh(orm)
        return rapor_schedule_to_entity(orm)

    def guncelle(self, schedule: RaporSchedule) -> RaporSchedule:
        orm = self._db.query(RaporScheduleORM).filter(RaporScheduleORM.id == schedule.id).first()
        if not orm:
            return None
        orm.sablon_id = schedule.sablon_id
        orm.sablon_adi = schedule.sablon_adi
        orm.periyod = schedule.periyod
        orm.saat = schedule.saat
        orm.alici_emailler = schedule.alici_emailler
        orm.format = schedule.format
        orm.is_aktif = schedule.is_aktif
        orm.son_calistirilma = schedule.son_calistirilma
        orm.guncelleme_tarihi = schedule.guncelleme_tarihi
        self._db.commit()
        self._db.refresh(orm)
        return rapor_schedule_to_entity(orm)

    def sil(self, schedule_id: int) -> bool:
        orm = self._db.query(RaporScheduleORM).filter(RaporScheduleORM.id == schedule_id).first()
        if not orm:
            return False
        self._db.delete(orm)
        self._db.commit()
        return True


# ════════════════════════════════════════════
# RAPOR VERİ SORGULARI
# ════════════════════════════════════════════

class SqlAlchemyRaporVeriRepository(IRaporVeriRepository):

    def __init__(self, db: Session):
        self._db = db

    def stok_verisi(self, urun_id: Optional[int] = None) -> List[Any]:
        query = self._db.query(
            Urun.id,
            Urun.isim,
            Urun.stok_miktari,
            Urun.min_stok,
            Marka.isim.label("marka"),
            Kategori.isim.label("kategori"),
        ).outerjoin(Marka).outerjoin(Kategori).filter(Urun.aktif)
        if urun_id:
            query = query.filter(Urun.id == urun_id)
        return query.all()

    def siparis_verisi(
        self, baslang_tarihi: Optional[date] = None,
        bitis_tarihi: Optional[date] = None,
    ) -> List[Any]:
        query = self._db.query(
            Siparis.siparis_no,
            Siparis.musteri_adi,
            Siparis.teslimat_tarihi,
            Siparis.durum,
            Siparis.top_miktar,
            Siparis.top_tutar,
            func.count(SiparisKalemi.id).label("kalem_sayisi"),
        ).outerjoin(SiparisKalemi).filter(Siparis.aktif)
        if baslang_tarihi:
            query = query.filter(Siparis.olusturma_tarihi >= baslang_tarihi)
        if bitis_tarihi:
            query = query.filter(Siparis.olusturma_tarihi <= bitis_tarihi)
        return query.group_by(Siparis.id).all()

    def hareket_verisi(
        self, baslang_tarihi: Optional[date] = None,
        bitis_tarihi: Optional[date] = None,
    ) -> List[Any]:
        query = self._db.query(
            StokHareketi.hareket_tipi,
            Urun.isim,
            StokHareketi.miktar,
            StokHareketi.tarih,
            Kullanici.ad_soyad,
        ).join(Urun).outerjoin(Kullanici)
        if baslang_tarihi:
            query = query.filter(StokHareketi.tarih >= baslang_tarihi)
        if bitis_tarihi:
            query = query.filter(StokHareketi.tarih <= bitis_tarihi)
        return query.order_by(StokHareketi.tarih.desc()).all()

    def kritik_stok(self) -> List[Dict[str, Any]]:
        rows = self._db.query(
            Urun.id,
            Urun.isim,
            Urun.stok_miktari,
            Urun.min_stok,
            Marka.isim.label("marka"),
            Kategori.isim.label("kategori"),
        ).outerjoin(Marka).outerjoin(Kategori).filter(
            Urun.aktif,
            Urun.stok_miktari <= Urun.min_stok,
        ).order_by(Urun.stok_miktari.asc()).all()
        return [dict(r._mapping) for r in rows]

    def skt_yaklasan(self, gun: int = 30) -> List[Dict[str, Any]]:
        sinir_tarihi = datetime.utcnow().date() + timedelta(days=gun)
        rows = self._db.query(
            Lot.id,
            Lot.lot_no,
            Lot.son_kullanma_tarihi,
            Urun.isim.label("urun_isim"),
            func.sum(Palet.koli_adedi).label("toplam_stok"),
        ).join(Urun).outerjoin(
            Palet, (Palet.lot_id == Lot.id) & (Palet.aktif),
        ).filter(
            Lot.aktif,
            Lot.son_kullanma_tarihi is not None,
            Lot.son_kullanma_tarihi <= sinir_tarihi,
            Lot.son_kullanma_tarihi >= datetime.utcnow().date(),
        ).group_by(
            Lot.id, Lot.lot_no, Lot.son_kullanma_tarihi, Urun.isim,
        ).order_by(Lot.son_kullanma_tarihi.asc()).all()
        return [dict(r._mapping) for r in rows]

    def abc_analiz(self) -> List[Dict[str, Any]]:
        satislar = self._db.query(
            SiparisKalemi.urun_id,
            Urun.isim.label("urun_isim"),
            func.sum(SiparisKalemi.toplam).label("toplam_deger"),
            func.sum(SiparisKalemi.miktar).label("toplam_miktar"),
        ).join(Urun).join(Siparis).filter(
            Siparis.aktif,
            Siparis.durum != "Iptal",
        ).group_by(SiparisKalemi.urun_id, Urun.isim).order_by(
            func.sum(SiparisKalemi.toplam).desc(),
        ).all()

        if not satislar:
            return []

        genel_toplam = sum(s.toplam_deger or 0 for s in satislar)
        if genel_toplam == 0:
            return []

        sonuclar = []
        kumulatif = 0.0
        for s in satislar:
            deger = s.toplam_deger or 0
            kumulatif += deger
            yuzde = (kumulatif / genel_toplam) * 100
            if yuzde <= 70:
                sinif = "A"
            elif yuzde <= 90:
                sinif = "B"
            else:
                sinif = "C"
            sonuclar.append({
                "urun_id": s.urun_id,
                "urun_isim": s.urun_isim,
                "toplam_deger": round(deger, 2),
                "toplam_miktar": s.toplam_miktar,
                "sinif": sinif,
            })
        return sonuclar

    def depo_doluluk(self) -> List[Dict[str, Any]]:
        palet_sayilari = self._db.query(
            Palet.raf_id,
            func.count(Palet.id).label("dolu"),
        ).filter(Palet.aktif).group_by(Palet.raf_id).subquery()

        sonuclar_raw = self._db.query(
            Raf.id,
            Raf.kod,
            Raf.kapasite,
            func.coalesce(palet_sayilari.c.dolu, 0).label("dolu"),
        ).outerjoin(
            palet_sayilari, Raf.id == palet_sayilari.c.raf_id,
        ).filter(Raf.aktif).all()

        return [
            {
                "raf_id": row.id,
                "raf_kodu": row.kod,
                "kapasite": row.kapasite,
                "dolu": row.dolu,
                "doluluk_yuzde": round((row.dolu / row.kapasite) * 100, 1) if row.kapasite > 0 else 0,
            }
            for row in sonuclar_raw
        ]
