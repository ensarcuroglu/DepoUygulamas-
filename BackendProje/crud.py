from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from datetime import datetime, timedelta, date

from models import (
    Marka, Kategori, Depo, Raf, Tedarikci,
    Urun, Lot, Palet, StokHareketi, Kullanici
)
from schemas import (
    MarkaCreate, MarkaUpdate,
    KategoriCreate, KategoriUpdate,
    DepoCreate, DepoUpdate,
    RafCreate, RafUpdate,
    TedarikciCreate, TedarikciUpdate,
    UrunCreate, UrunUpdate,
    LotCreate, LotUpdate,
    PaletCreate, PaletUpdate,
    StokHareketiCreate
)


# ========================
# MARKA CRUD
# ========================

def get_markalar(db: Session, skip: int = 0, limit: int = 100, sadece_aktif: bool = True):
    query = db.query(Marka)
    if sadece_aktif:
        query = query.filter(Marka.aktif == True)
    return query.offset(skip).limit(limit).all()

def get_marka(db: Session, marka_id: int):
    return db.query(Marka).filter(Marka.id == marka_id).first()

def create_marka(db: Session, marka: MarkaCreate):
    db_marka = Marka(**marka.model_dump())
    db.add(db_marka)
    db.commit()
    db.refresh(db_marka)
    return db_marka

def update_marka(db: Session, marka_id: int, marka: MarkaUpdate):
    db_marka = db.query(Marka).filter(Marka.id == marka_id).first()
    if not db_marka:
        return None
    for key, value in marka.model_dump(exclude_unset=True).items():
        setattr(db_marka, key, value)
    db.commit()
    db.refresh(db_marka)
    return db_marka

def delete_marka(db: Session, marka_id: int):
    db_marka = db.query(Marka).filter(Marka.id == marka_id).first()
    if not db_marka:
        return False
    db_marka.aktif = False
    db.commit()
    return True


# ========================
# KATEGORİ CRUD
# ========================

def get_kategoriler(db: Session, skip: int = 0, limit: int = 100, sadece_aktif: bool = True):
    query = db.query(Kategori)
    if sadece_aktif:
        query = query.filter(Kategori.aktif == True)
    return query.offset(skip).limit(limit).all()

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
    for key, value in kategori.model_dump(exclude_unset=True).items():
        setattr(db_kategori, key, value)
    db.commit()
    db.refresh(db_kategori)
    return db_kategori

def delete_kategori(db: Session, kategori_id: int):
    db_kategori = db.query(Kategori).filter(Kategori.id == kategori_id).first()
    if not db_kategori:
        return False
    db_kategori.aktif = False
    db.commit()
    return True


# ========================
# DEPO CRUD
# ========================

def get_depolar(db: Session, skip: int = 0, limit: int = 100, sadece_aktif: bool = True):
    query = db.query(Depo)
    if sadece_aktif:
        query = query.filter(Depo.aktif == True)
    return query.offset(skip).limit(limit).all()

def get_depo(db: Session, depo_id: int):
    return db.query(Depo).filter(Depo.id == depo_id).first()

def create_depo(db: Session, depo: DepoCreate):
    db_depo = Depo(**depo.model_dump())
    db.add(db_depo)
    db.commit()
    db.refresh(db_depo)
    return db_depo

def update_depo(db: Session, depo_id: int, depo: DepoUpdate):
    db_depo = db.query(Depo).filter(Depo.id == depo_id).first()
    if not db_depo:
        return None
    for key, value in depo.model_dump(exclude_unset=True).items():
        setattr(db_depo, key, value)
    db.commit()
    db.refresh(db_depo)
    return db_depo

def delete_depo(db: Session, depo_id: int):
    db_depo = db.query(Depo).filter(Depo.id == depo_id).first()
    if not db_depo:
        return False
    db_depo.aktif = False
    db.commit()
    return True


# ========================
# RAF CRUD
# ========================

def get_raflar(db: Session, skip: int = 0, limit: int = 100, depo_id: int = None, sadece_aktif: bool = True):
    query = db.query(Raf)
    if sadece_aktif:
        query = query.filter(Raf.aktif == True)
    if depo_id:
        query = query.filter(Raf.depo_id == depo_id)
    return query.offset(skip).limit(limit).all()

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
    for key, value in raf.model_dump(exclude_unset=True).items():
        setattr(db_raf, key, value)
    db.commit()
    db.refresh(db_raf)
    return db_raf

def delete_raf(db: Session, raf_id: int):
    db_raf = db.query(Raf).filter(Raf.id == raf_id).first()
    if not db_raf:
        return False
    db_raf.aktif = False
    db.commit()
    return True


# ========================
# TEDARİKÇİ CRUD
# ========================

def get_tedarikciler(db: Session, skip: int = 0, limit: int = 100, sadece_aktif: bool = True):
    query = db.query(Tedarikci)
    if sadece_aktif:
        query = query.filter(Tedarikci.aktif == True)
    return query.offset(skip).limit(limit).all()

def get_tedarikci(db: Session, tedarikci_id: int):
    return db.query(Tedarikci).filter(Tedarikci.id == tedarikci_id).first()

def create_tedarikci(db: Session, tedarikci: TedarikciCreate):
    db_tedarikci = Tedarikci(**tedarikci.model_dump())
    db.add(db_tedarikci)
    db.commit()
    db.refresh(db_tedarikci)
    return db_tedarikci

def update_tedarikci(db: Session, tedarikci_id: int, tedarikci: TedarikciUpdate):
    db_tedarikci = db.query(Tedarikci).filter(Tedarikci.id == tedarikci_id).first()
    if not db_tedarikci:
        return None
    for key, value in tedarikci.model_dump(exclude_unset=True).items():
        setattr(db_tedarikci, key, value)
    db.commit()
    db.refresh(db_tedarikci)
    return db_tedarikci

def delete_tedarikci(db: Session, tedarikci_id: int):
    db_tedarikci = db.query(Tedarikci).filter(Tedarikci.id == tedarikci_id).first()
    if not db_tedarikci:
        return False
    db_tedarikci.aktif = False
    db.commit()
    return True


# ========================
# ÜRÜN CRUD
# ========================

def get_urunler(db: Session, skip: int = 0, limit: int = 50, search: str = None,
                kategori_id: int = None, marka_id: int = None, sadece_aktif: bool = True):
    query = db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori)
    )

    if sadece_aktif:
        query = query.filter(Urun.aktif == True)

    if search:
        query = query.filter(
            or_(
                Urun.isim.ilike(f"%{search}%"),
                Urun.barkod.ilike(f"%{search}%"),
                Urun.ean.ilike(f"%{search}%"),
                Urun.aciklama.ilike(f"%{search}%")
            )
        )

    if kategori_id:
        query = query.filter(Urun.kategori_id == kategori_id)

    if marka_id:
        query = query.filter(Urun.marka_id == marka_id)

    return query.offset(skip).limit(limit).all()

def get_urun(db: Session, urun_id: int):
    return db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori),
        joinedload(Urun.tedarikci)
    ).filter(Urun.id == urun_id).first()

def get_urun_by_barkod(db: Session, barkod: str):
    return db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori)
    ).filter(
        or_(Urun.barkod == barkod, Urun.ean == barkod)
    ).first()

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
    for key, value in urun.model_dump(exclude_unset=True).items():
        setattr(db_urun, key, value)
    db_urun.guncelleme_tarihi = datetime.utcnow()
    db.commit()
    db.refresh(db_urun)
    return db_urun

def delete_urun(db: Session, urun_id: int):
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        return False
    db_urun.aktif = False
    db_urun.guncelleme_tarihi = datetime.utcnow()
    db.commit()
    return True

def get_kritik_urunler(db: Session):
    """Min stok seviyesinin altındaki ürünleri getirir"""
    return db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori)
    ).filter(
        Urun.aktif == True,
        Urun.stok_miktari <= Urun.min_stok
    ).all()


# ========================
# LOT CRUD
# ========================

def get_lotlar(db: Session, skip: int = 0, limit: int = 50, urun_id: int = None, sadece_aktif: bool = True):
    query = db.query(Lot).options(joinedload(Lot.urun))
    if sadece_aktif:
        query = query.filter(Lot.aktif == True)
    if urun_id:
        query = query.filter(Lot.urun_id == urun_id)
    return query.order_by(Lot.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

def get_lot(db: Session, lot_id: int):
    return db.query(Lot).options(
        joinedload(Lot.urun),
        joinedload(Lot.paletler)
    ).filter(Lot.id == lot_id).first()

def get_lot_by_no(db: Session, lot_no: str):
    return db.query(Lot).options(
        joinedload(Lot.urun),
        joinedload(Lot.paletler)
    ).filter(Lot.lot_no == lot_no).first()

def create_lot(db: Session, lot: LotCreate):
    db_lot = Lot(**lot.model_dump())
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot

def update_lot(db: Session, lot_id: int, lot: LotUpdate):
    db_lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not db_lot:
        return None
    for key, value in lot.model_dump(exclude_unset=True).items():
        setattr(db_lot, key, value)
    db.commit()
    db.refresh(db_lot)
    return db_lot

def delete_lot(db: Session, lot_id: int):
    db_lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not db_lot:
        return False
    db_lot.aktif = False
    db.commit()
    return True

def get_skt_yaklasan_lotlar(db: Session, gun: int = 30):
    """SKT'si belirtilen gün içinde dolacak lotları getirir"""
    sinir_tarih = date.today() + timedelta(days=gun)
    return db.query(Lot).options(
        joinedload(Lot.urun)
    ).filter(
        Lot.aktif == True,
        Lot.son_kullanma_tarihi != None,
        Lot.son_kullanma_tarihi <= sinir_tarih
    ).order_by(Lot.son_kullanma_tarihi.asc()).all()


# ========================
# PALET CRUD
# ========================

def get_paletler(db: Session, skip: int = 0, limit: int = 50, lot_id: int = None,
                 raf_id: int = None, sadece_aktif: bool = True):
    query = db.query(Palet).options(
        joinedload(Palet.lot),
        joinedload(Palet.raf)
    )
    if sadece_aktif:
        query = query.filter(Palet.aktif == True)
    if lot_id:
        query = query.filter(Palet.lot_id == lot_id)
    if raf_id:
        query = query.filter(Palet.raf_id == raf_id)
    return query.order_by(Palet.tarih.desc()).offset(skip).limit(limit).all()

def get_palet(db: Session, palet_id: int):
    return db.query(Palet).options(
        joinedload(Palet.lot).joinedload(Lot.urun),
        joinedload(Palet.raf)
    ).filter(Palet.id == palet_id).first()

def get_palet_by_no(db: Session, palet_no: str):
    return db.query(Palet).options(
        joinedload(Palet.lot).joinedload(Lot.urun),
        joinedload(Palet.raf)
    ).filter(Palet.palet_no == palet_no).first()

def create_palet(db: Session, palet: PaletCreate):
    db_palet = Palet(**palet.model_dump())
    db.add(db_palet)
    db.commit()
    db.refresh(db_palet)
    return db_palet

def update_palet(db: Session, palet_id: int, palet: PaletUpdate):
    db_palet = db.query(Palet).filter(Palet.id == palet_id).first()
    if not db_palet:
        return None
    for key, value in palet.model_dump(exclude_unset=True).items():
        setattr(db_palet, key, value)
    db.commit()
    db.refresh(db_palet)
    return db_palet

def delete_palet(db: Session, palet_id: int):
    """Paleti pasife alır (depodan çıkarır)"""
    db_palet = db.query(Palet).filter(Palet.id == palet_id).first()
    if not db_palet:
        return False
    db_palet.aktif = False
    db.commit()
    return True

def get_sonraki_palet_no(db: Session):
    """Bir sonraki palet numarasını üretir (1000001, 1000002, ...)"""
    son_palet = db.query(Palet).order_by(Palet.id.desc()).first()
    if son_palet and son_palet.palet_no.isdigit():
        return str(int(son_palet.palet_no) + 1)
    return "1000001"


# ========================
# STOK HAREKETİ CRUD
# ========================

def get_stok_hareketleri(db: Session, skip: int = 0, limit: int = 50, urun_id: int = None, lot_id: int = None):
    query = db.query(StokHareketi).order_by(StokHareketi.tarih.desc())
    if urun_id:
        query = query.filter(StokHareketi.urun_id == urun_id)
    if lot_id:
        query = query.filter(StokHareketi.lot_id == lot_id)
    return query.offset(skip).limit(limit).all()

def create_stok_hareketi(db: Session, hareket: StokHareketiCreate, kullanici_id: int = None):
    """Stok hareketi oluşturur. Palet bazlı çıkış yapılıyorsa paleti pasife alır."""
    db_hareket = StokHareketi(
        **hareket.model_dump(),
        kullanici_id=kullanici_id
    )
    db.add(db_hareket)

    # Çıkış hareketi ve palet belirtilmişse paleti pasife al
    if hareket.hareket_tipi == "cikis" and hareket.palet_id:
        db_palet = db.query(Palet).filter(Palet.id == hareket.palet_id).first()
        if db_palet:
            db_palet.aktif = False

    db.commit()
    db.refresh(db_hareket)
    return db_hareket


# ========================
# DASHBOARD İSTATİSTİKLERİ
# ========================

def get_dashboard_stats(db: Session):
    toplam_urun = db.query(func.count(Urun.id)).filter(Urun.aktif == True).scalar()

    # Kritik stok: SQL sorgusu ile hesaplanır
    kritik_stok = db.query(func.count(Urun.id)).filter(
        Urun.aktif == True,
        Urun.stok_miktari <= Urun.min_stok
    ).scalar()

    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    bugunku_hareket = db.query(func.count(StokHareketi.id)).filter(
        StokHareketi.tarih >= bugun
    ).scalar()

    # Toplam değer: SQL fonksiyonu ile sum(fiyat * stok) hesaplanır
    toplam_deger = db.query(func.coalesce(func.sum(Urun.stok_miktari * Urun.fiyat), 0.0)).filter(Urun.aktif == True).scalar()

    return {
        "toplam_urun": toplam_urun,
        "kritik_stok_sayisi": kritik_stok,
        "bugunku_hareket": bugunku_hareket,
        "toplam_deger": round(toplam_deger, 2)
    }
