from sqlalchemy.orm import Session
from models import Depo, SistemLog
from schemas import DepoCreate, DepoUpdate


def get_depolar(db: Session, skip: int = 0, limit: int = 100, sadece_aktif: bool = True):
    query = db.query(Depo)
    if sadece_aktif:
        query = query.filter(Depo.aktif == True)
    return query.offset(skip).limit(limit).all()

def get_depo(db: Session, depo_id: int):
    return db.query(Depo).filter(Depo.id == depo_id).first()

def create_depo(db: Session, depo: DepoCreate, kullanici_id: int):
    db_depo = Depo(**depo.model_dump())
    db.add(db_depo)
    db.flush()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Depo Yönetimi",
        detay=f"Yeni depo eklendi: {db_depo.isim}"
    )
    db.add(log)
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
