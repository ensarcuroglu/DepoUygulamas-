from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from models import DestekTalebi, SistemLog
from schemas import DestekTalebiCreate, DestekTalebiUpdate


def get_destek_talepleri(db: Session, skip: int = 0, limit: int = 100, kullanici_id: int = None, durum: str = None):
    query = db.query(DestekTalebi).options(joinedload(DestekTalebi.kullanici))
    if kullanici_id:
        query = query.filter(DestekTalebi.kullanici_id == kullanici_id)
    if durum:
        query = query.filter(DestekTalebi.durum == durum)
    return query.order_by(DestekTalebi.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

def get_destek_talebi(db: Session, talep_id: int):
    return db.query(DestekTalebi).options(joinedload(DestekTalebi.kullanici)).filter(DestekTalebi.id == talep_id).first()

def create_destek_talebi(db: Session, talep: DestekTalebiCreate, kullanici_id: int):
    db_talep = DestekTalebi(**talep.model_dump(), kullanici_id=kullanici_id)
    db.add(db_talep)
    db.commit()
    db.refresh(db_talep)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Destek Masası",
        detay=f"Yeni destek talebi oluşturuldu: {db_talep.konu}"
    )
    db.add(log)
    db.commit()

    return db_talep

def update_destek_talebi(db: Session, talep_id: int, talep_update: DestekTalebiUpdate, admin_id: int):
    db_talep = db.query(DestekTalebi).filter(DestekTalebi.id == talep_id).first()
    if not db_talep:
        return None

    eski_durum = db_talep.durum

    for key, value in talep_update.model_dump(exclude_unset=True).items():
        setattr(db_talep, key, value)

    db_talep.guncelleme_tarihi = datetime.utcnow()

    log = SistemLog(
        kullanici_id=admin_id,
        islem_tipi="UPDATE",
        modul="Destek Masası",
        detay=f"Destek talebi güncellendi (#{db_talep.id}). Durum: {eski_durum} -> {db_talep.durum}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_talep)
    return db_talep
