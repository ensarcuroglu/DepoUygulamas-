from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import datetime
from fastapi.encoders import jsonable_encoder

from models import Urun, SistemLog
from schemas import UrunCreate, UrunUpdate


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

def create_urun(db: Session, urun: UrunCreate, kullanici_id: int):
    db_urun = Urun(**urun.model_dump())
    db.add(db_urun)
    db.commit()
    db.refresh(db_urun)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Ürün Yönetimi",
        detay=f"Yeni ürün eklendi: {urun.isim} (Barkod: {urun.barkod or '-'})",
        yeni_veri=jsonable_encoder(urun.model_dump())
    )
    db.add(log)
    db.commit()

    return db_urun

def update_urun(db: Session, urun_id: int, urun: UrunUpdate, kullanici_id: int):
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        return None

    eski_veri = {c.name: getattr(db_urun, c.name) for c in db_urun.__table__.columns}

    for key, value in urun.model_dump(exclude_unset=True).items():
        setattr(db_urun, key, value)
    db_urun.guncelleme_tarihi = datetime.utcnow()
    db.commit()
    db.refresh(db_urun)

    yeni_veri = {c.name: getattr(db_urun, c.name) for c in db_urun.__table__.columns}

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="UPDATE",
        modul="Ürün Yönetimi",
        detay=f"Ürün güncellendi: {db_urun.isim}",
        eski_veri=jsonable_encoder({"isim": eski_veri['isim'], "fiyat": eski_veri['fiyat'], "stok": db_urun.stok_miktari}),
        yeni_veri=jsonable_encoder({"isim": yeni_veri['isim'], "fiyat": yeni_veri['fiyat'], "stok": db_urun.stok_miktari})
    )
    db.add(log)
    db.commit()

    return db_urun

def delete_urun(db: Session, urun_id: int, kullanici_id: int):
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        return False

    db_urun.aktif = False
    db_urun.guncelleme_tarihi = datetime.utcnow()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="DELETE",
        modul="Ürün Yönetimi",
        detay=f"Ürün silindi (pasife alındı): {db_urun.isim}"
    )
    db.add(log)

    db.commit()
    return True

def get_kritik_urunler(db: Session):
    """Min stok seviyesinin altindaki urunleri getirir"""
    return db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori)
    ).filter(
        Urun.aktif == True,
        Urun.stok_miktari <= Urun.min_stok
    ).all()
