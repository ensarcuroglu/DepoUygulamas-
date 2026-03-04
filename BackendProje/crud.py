from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, timedelta

from models import Urun, Kategori, Raf, StokHareketi, Kullanici, Tedarikci
from schemas import (
    UrunCreate, UrunUpdate,
    KategoriCreate, KategoriUpdate,
    RafCreate, RafUpdate,
    StokHareketiCreate,
    KullaniciCreate, TedarikciCreate
)


# ========================
# KATEGORİ CRUD
# ========================

def get_kategoriler(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Kategori).offset(skip).limit(limit).all()

def get_kategori(db: Session, kategori_id: int):
    return db.query(Kategori).filter(Kategori.id == kategori_id).first()

def create_kategori(db: Session, kategori: KategoriCreate):
    db_kategori = Kategori(**kategori.model_dump())
    db.add(db_kategori)
    db.commit()
    db.refresh(db_kategori)
    return db_kategori

def update_kategori(db: Session, kategori_id: int, kategori: KategoriUpdate):
    db_kategori = db.query(Kategori).filter(Kategori.id == kategori_id).first()
    if not db_kategori:
        return None
    update_data = kategori.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_kategori, key, value)
    db.commit()
    db.refresh(db_kategori)
    return db_kategori

def delete_kategori(db: Session, kategori_id: int):
    db_kategori = db.query(Kategori).filter(Kategori.id == kategori_id).first()
    if not db_kategori:
        return False
    db.delete(db_kategori)
    db.commit()
    return True


# ========================
# RAF CRUD
# ========================

def get_raflar(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Raf).offset(skip).limit(limit).all()

def get_raf(db: Session, raf_id: int):
    return db.query(Raf).filter(Raf.id == raf_id).first()

def create_raf(db: Session, raf: RafCreate):
    db_raf = Raf(**raf.model_dump())
    db.add(db_raf)
    db.commit()
    db.refresh(db_raf)
    return db_raf

def update_raf(db: Session, raf_id: int, raf: RafUpdate):
    db_raf = db.query(Raf).filter(Raf.id == raf_id).first()
    if not db_raf:
        return None
    update_data = raf.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_raf, key, value)
    db.commit()
    db.refresh(db_raf)
    return db_raf

def delete_raf(db: Session, raf_id: int):
    db_raf = db.query(Raf).filter(Raf.id == raf_id).first()
    if not db_raf:
        return False
    db.delete(db_raf)
    db.commit()
    return True


# ========================
# ÜRÜN CRUD
# ========================

def get_urunler(db: Session, skip: int = 0, limit: int = 50, search: str = None, kategori_id: int = None):
    query = db.query(Urun)

    # Arama filtresi
    if search:
        query = query.filter(
            or_(
                Urun.isim.ilike(f"%{search}%"),
                Urun.barkod.ilike(f"%{search}%"),
                Urun.aciklama.ilike(f"%{search}%")
            )
        )

    # Kategori filtresi
    if kategori_id:
        query = query.filter(Urun.kategori_id == kategori_id)

    return query.offset(skip).limit(limit).all()

def get_urun(db: Session, urun_id: int):
    return db.query(Urun).filter(Urun.id == urun_id).first()

def get_urun_by_barkod(db: Session, barkod: str):
    return db.query(Urun).filter(Urun.barkod == barkod).first()

def create_urun(db: Session, urun: UrunCreate):
    db_urun = Urun(**urun.model_dump())
    db.add(db_urun)
    db.commit()
    db.refresh(db_urun)
    return db_urun

def update_urun(db: Session, urun_id: int, urun: UrunUpdate):
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        return None
    update_data = urun.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_urun, key, value)
    db_urun.guncelleme_tarihi = datetime.utcnow()
    db.commit()
    db.refresh(db_urun)
    return db_urun

def delete_urun(db: Session, urun_id: int):
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        return False
    db.delete(db_urun)
    db.commit()
    return True

def get_kritik_urunler(db: Session):
    """Min stok seviyesinin altındaki ürünleri getirir"""
    return db.query(Urun).filter(Urun.stok_miktari <= Urun.min_stok).all()


# ========================
# STOK HAREKETİ CRUD
# ========================

def get_stok_hareketleri(db: Session, skip: int = 0, limit: int = 50, urun_id: int = None):
    query = db.query(StokHareketi).order_by(StokHareketi.tarih.desc())
    if urun_id:
        query = query.filter(StokHareketi.urun_id == urun_id)
    return query.offset(skip).limit(limit).all()

def create_stok_hareketi(db: Session, hareket: StokHareketiCreate, kullanici_id: int = None):
    """Stok hareketi oluşturur ve ürün stok miktarını günceller"""
    # Hareketi kaydet
    db_hareket = StokHareketi(
        **hareket.model_dump(),
        kullanici_id=kullanici_id
    )
    db.add(db_hareket)

    # Ürün stok miktarını güncelle
    db_urun = db.query(Urun).filter(Urun.id == hareket.urun_id).first()
    if db_urun:
        if hareket.hareket_tipi == "giris":
            db_urun.stok_miktari += hareket.miktar
        elif hareket.hareket_tipi == "cikis":
            db_urun.stok_miktari -= hareket.miktar
        db_urun.guncelleme_tarihi = datetime.utcnow()

    db.commit()
    db.refresh(db_hareket)
    return db_hareket


# ========================
# DASHBOARD İSTATİSTİKLERİ
# ========================

def get_dashboard_stats(db: Session):
    toplam_urun = db.query(func.count(Urun.id)).scalar()
    kritik_stok = db.query(func.count(Urun.id)).filter(
        Urun.stok_miktari <= Urun.min_stok
    ).scalar()

    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    bugunku_hareket = db.query(func.count(StokHareketi.id)).filter(
        StokHareketi.tarih >= bugun
    ).scalar()

    toplam_deger = db.query(
        func.sum(Urun.stok_miktari * Urun.fiyat)
    ).scalar() or 0.0

    return {
        "toplam_urun": toplam_urun,
        "kritik_stok_sayisi": kritik_stok,
        "bugunku_hareket": bugunku_hareket,
        "toplam_deger": round(toplam_deger, 2)
    }


# ========================
# Tedarikçi CRUD
# ========================
def get_tedarikciler(db: Session, skip: int = 0, limit: int = 100):
    """Tedarikçi listesini getirir"""
    return db.query(Tedarikci).offset(skip).limit(limit).all()

def create_tedarikci(db: Session, tedarikci: TedarikciCreate):
    """Yeni tedarikçi oluşturur"""
    db_tedarikci = Tedarikci(**tedarikci.model_dump())
    db.add(db_tedarikci)
    db.commit()
    db.refresh(db_tedarikci)
    return db_tedarikci