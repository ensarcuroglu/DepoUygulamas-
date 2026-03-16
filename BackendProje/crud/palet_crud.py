from sqlalchemy.orm import Session, joinedload

from models import Palet, Lot
from schemas import PaletCreate, PaletUpdate


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
    """Paleti pasife alir (depodan cikarir)"""
    db_palet = db.query(Palet).filter(Palet.id == palet_id).first()
    if not db_palet:
        return False
    db_palet.aktif = False
    db.commit()
    return True

def get_sonraki_palet_no(db: Session):
    """Bir sonraki palet numarasini uretir (1000001, 1000002, ...)"""
    son_palet = db.query(Palet).order_by(Palet.id.desc()).first()
    if son_palet and son_palet.palet_no.isdigit():
        return str(int(son_palet.palet_no) + 1)
    return "1000001"
