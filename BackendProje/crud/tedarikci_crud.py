from sqlalchemy.orm import Session
from models import Tedarikci
from schemas import TedarikciCreate, TedarikciUpdate


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
