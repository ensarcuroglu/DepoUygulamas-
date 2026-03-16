from sqlalchemy.orm import Session
from models import Marka
from schemas import MarkaCreate, MarkaUpdate


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
