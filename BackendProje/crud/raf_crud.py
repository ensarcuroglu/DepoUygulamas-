from sqlalchemy.orm import Session
from models import Raf
from schemas import RafCreate, RafUpdate


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
