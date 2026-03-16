from sqlalchemy.orm import Session, joinedload
from datetime import date, timedelta

from models import Lot
from schemas import LotCreate, LotUpdate


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
    """SKT'si belirtilen gun icinde dolacak lotlari getirir"""
    sinir_tarih = date.today() + timedelta(days=gun)
    return db.query(Lot).options(
        joinedload(Lot.urun)
    ).filter(
        Lot.aktif == True,
        Lot.son_kullanma_tarihi != None,
        Lot.son_kullanma_tarihi <= sinir_tarih
    ).order_by(Lot.son_kullanma_tarihi.asc()).all()
