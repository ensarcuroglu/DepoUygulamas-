from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from datetime import datetime, date, timedelta

from models import (
    RaporSablonu, RaporLogu, RaporSchedule, SistemLog,
    Urun, Marka, Kategori, Siparis, SiparisKalemi,
    StokHareketi, Kullanici, Lot, Palet, Raf
)
from schemas import (
    RaporSablonuCreate, RaporSablonuUpdate,
    RaporLoguCreate,
    RaporScheduleCreate, RaporScheduleUpdate
)


# ========================
# RAPOR SABLONU CRUD
# ========================

def get_rapor_sablonlari(db: Session, skip: int = 0, limit: int = 100, tur: str = None, is_aktif: bool = True):
    query = db.query(RaporSablonu)
    if is_aktif:
        query = query.filter(RaporSablonu.is_aktif == True)
    if tur:
        query = query.filter(RaporSablonu.tur == tur)
    return query.order_by(RaporSablonu.ad).offset(skip).limit(limit).all()

def get_rapor_sablonu(db: Session, sablon_id: int):
    return db.query(RaporSablonu).filter(RaporSablonu.id == sablon_id).first()

def create_rapor_sablonu(db: Session, sablon: RaporSablonuCreate, kullanici_id: int):
    db_sablon = RaporSablonu(
        **sablon.model_dump(),
        olusturan_kullanici_id=kullanici_id
    )
    db.add(db_sablon)
    db.flush()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Rapor Yönetimi",
        detay=f"Yeni rapor şablonu oluşturuldu: {db_sablon.ad} ({db_sablon.tur})"
    )
    db.add(log)

    db.commit()
    db.refresh(db_sablon)
    return db_sablon

def update_rapor_sablonu(db: Session, sablon_id: int, sablon_update: RaporSablonuUpdate, kullanici_id: int):
    db_sablon = db.query(RaporSablonu).filter(RaporSablonu.id == sablon_id).first()
    if not db_sablon:
        return None

    for key, value in sablon_update.model_dump(exclude_unset=True).items():
        setattr(db_sablon, key, value)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="UPDATE",
        modul="Rapor Yönetimi",
        detay=f"Rapor şablonu güncellendi: {db_sablon.ad}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_sablon)
    return db_sablon

def delete_rapor_sablonu(db: Session, sablon_id: int, kullanici_id: int):
    db_sablon = db.query(RaporSablonu).filter(RaporSablonu.id == sablon_id).first()
    if not db_sablon:
        return False

    db_sablon.is_aktif = False

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="DELETE",
        modul="Rapor Yönetimi",
        detay=f"Rapor şablonu silindi: {db_sablon.ad}"
    )
    db.add(log)

    db.commit()
    return True


# ========================
# RAPOR LOGU CRUD
# ========================

def get_rapor_loglari(db: Session, skip: int = 0, limit: int = 100, sablon_id: int = None):
    query = db.query(RaporLogu).options(joinedload(RaporLogu.sablon))
    if sablon_id:
        query = query.filter(RaporLogu.sablon_id == sablon_id)
    return query.order_by(RaporLogu.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

def create_rapor_logu(db: Session, log_data: RaporLoguCreate, kullanici_id: int):
    db_log = RaporLogu(
        **log_data.model_dump(),
        kullanici_id=kullanici_id,
        tamamlanma_tarihi=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


# ========================
# RAPOR SCHEDULE CRUD
# ========================

def get_rapor_schedules(db: Session, skip: int = 0, limit: int = 100, is_aktif: bool = True):
    query = db.query(RaporSchedule).options(joinedload(RaporSchedule.sablon))
    if is_aktif:
        query = query.filter(RaporSchedule.is_aktif == True)
    return query.order_by(RaporSchedule.sablon_adi).offset(skip).limit(limit).all()

def get_rapor_schedule(db: Session, schedule_id: int):
    return db.query(RaporSchedule).options(joinedload(RaporSchedule.sablon)).filter(RaporSchedule.id == schedule_id).first()

def create_rapor_schedule(db: Session, schedule: RaporScheduleCreate, kullanici_id: int):
    db_schedule = RaporSchedule(**schedule.model_dump())
    db.add(db_schedule)
    db.flush()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Rapor Zamanlaması",
        detay=f"Yeni zamanlı rapor oluşturuldu: {db_schedule.sablon_adi} ({db_schedule.periyod})"
    )
    db.add(log)

    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def update_rapor_schedule(db: Session, schedule_id: int, schedule_update: RaporScheduleUpdate, kullanici_id: int):
    db_schedule = db.query(RaporSchedule).filter(RaporSchedule.id == schedule_id).first()
    if not db_schedule:
        return None

    for key, value in schedule_update.model_dump(exclude_unset=True).items():
        setattr(db_schedule, key, value)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="UPDATE",
        modul="Rapor Zamanlaması",
        detay=f"Zamanlı rapor güncellendi: {db_schedule.sablon_adi}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_schedule)
    return db_schedule

def delete_rapor_schedule(db: Session, schedule_id: int, kullanici_id: int):
    db_schedule = db.query(RaporSchedule).filter(RaporSchedule.id == schedule_id).first()
    if not db_schedule:
        return False

    db.delete(db_schedule)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="DELETE",
        modul="Rapor Zamanlaması",
        detay=f"Zamanlı rapor silindi: {db_schedule.sablon_adi}"
    )
    db.add(log)

    db.commit()
    return True


# ========================
# RAPOR VERI URETIMI
# ========================

def get_stok_raporu_verileri(db: Session, urun_id: int = None):
    """Stok durumu raporu icin veri dondur"""
    query = db.query(
        Urun.id,
        Urun.isim,
        Urun.stok_miktari,
        Urun.min_stok,
        Marka.isim.label("marka"),
        Kategori.isim.label("kategori")
    ).outerjoin(Marka).outerjoin(Kategori).filter(Urun.aktif == True)

    if urun_id:
        query = query.filter(Urun.id == urun_id)

    return query.all()

def get_siparis_raporu_verileri(db: Session, baslang_tarihi: date = None, bitis_tarihi: date = None):
    """Siparis raporu icin veri dondur"""
    query = db.query(
        Siparis.siparis_no,
        Siparis.musteri_adi,
        Siparis.teslimat_tarihi,
        Siparis.durum,
        Siparis.top_miktar,
        Siparis.top_tutar,
        func.count(SiparisKalemi.id).label("kalem_sayisi")
    ).outerjoin(SiparisKalemi).filter(Siparis.aktif == True)

    if baslang_tarihi:
        query = query.filter(Siparis.olusturma_tarihi >= baslang_tarihi)
    if bitis_tarihi:
        query = query.filter(Siparis.olusturma_tarihi <= bitis_tarihi)

    return query.group_by(Siparis.id).all()

def get_hareket_raporu_verileri(db: Session, baslang_tarihi: date = None, bitis_tarihi: date = None):
    """Stok hareketi raporu icin veri dondur"""
    query = db.query(
        StokHareketi.hareket_tipi,
        Urun.isim,
        StokHareketi.miktar,
        StokHareketi.tarih,
        Kullanici.ad_soyad
    ).join(Urun).outerjoin(Kullanici)

    if baslang_tarihi:
        query = query.filter(StokHareketi.tarih >= baslang_tarihi)
    if bitis_tarihi:
        query = query.filter(StokHareketi.tarih <= bitis_tarihi)

    return query.order_by(StokHareketi.tarih.desc()).all()


def get_kritik_stok_raporu(db: Session):
    """Min stok seviyesinin altindaki urunleri dondur"""
    return db.query(
        Urun.id,
        Urun.isim,
        Urun.stok_miktari,
        Urun.min_stok,
        Marka.isim.label("marka"),
        Kategori.isim.label("kategori")
    ).outerjoin(Marka).outerjoin(Kategori).filter(
        Urun.aktif == True,
        Urun.stok_miktari <= Urun.min_stok
    ).order_by(Urun.stok_miktari.asc()).all()


def get_skt_raporu(db: Session, gun: int = 30):
    """Son kullanma tarihi yaklasan lotlari dondur (varsayilan: 30 gun icinde)"""
    sinir_tarihi = datetime.utcnow().date() + timedelta(days=gun)
    return db.query(
        Lot.id,
        Lot.lot_no,
        Lot.son_kullanma_tarihi,
        Urun.isim.label("urun_isim"),
        func.sum(Palet.koli_adedi).label("toplam_stok")
    ).join(Urun).outerjoin(
        Palet, (Palet.lot_id == Lot.id) & (Palet.aktif == True)
    ).filter(
        Lot.aktif == True,
        Lot.son_kullanma_tarihi != None,
        Lot.son_kullanma_tarihi <= sinir_tarihi,
        Lot.son_kullanma_tarihi >= datetime.utcnow().date()
    ).group_by(Lot.id, Lot.lot_no, Lot.son_kullanma_tarihi, Urun.isim).order_by(Lot.son_kullanma_tarihi.asc()).all()


def get_abc_analiz(db: Session):
    """
    ABC analizi: siparislerdeki toplam satis degerine gore urunleri A/B/C olarak siniflandir.
    A: Ilk %70 deger, B: Sonraki %20, C: Kalan %10.
    """
    satislar = db.query(
        SiparisKalemi.urun_id,
        Urun.isim.label("urun_isim"),
        func.sum(SiparisKalemi.toplam).label("toplam_deger"),
        func.sum(SiparisKalemi.miktar).label("toplam_miktar")
    ).join(Urun).join(Siparis).filter(
        Siparis.aktif == True,
        Siparis.durum != "Iptal"
    ).group_by(SiparisKalemi.urun_id, Urun.isim).order_by(
        func.sum(SiparisKalemi.toplam).desc()
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
            "sinif": sinif
        })

    return sonuclar


def get_depo_doluluk(db: Session):
    """Depo doluluk yuzdesini raf bazinda hesaplar"""
    raflar = db.query(Raf).filter(Raf.aktif == True).all()
    sonuclar = []
    for raf in raflar:
        aktif_palet_sayisi = db.query(func.count(Palet.id)).filter(
            Palet.raf_id == raf.id,
            Palet.aktif == True
        ).scalar() or 0
        doluluk_yuzde = round((aktif_palet_sayisi / raf.kapasite) * 100, 1) if raf.kapasite > 0 else 0
        sonuclar.append({
            "raf_id": raf.id,
            "raf_kodu": raf.kod,
            "kapasite": raf.kapasite,
            "dolu": aktif_palet_sayisi,
            "doluluk_yuzde": doluluk_yuzde
        })
    return sonuclar
