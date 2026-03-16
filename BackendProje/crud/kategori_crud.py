from sqlalchemy.orm import Session
from models import Kategori, SistemLog
from schemas import KategoriCreate, KategoriUpdate


def get_kategoriler(db: Session, skip: int = 0, limit: int = 100, sadece_aktif: bool = True):
    query = db.query(Kategori)
    if sadece_aktif:
        query = query.filter(Kategori.aktif == True)
    return query.offset(skip).limit(limit).all()

def get_kategori(db: Session, kategori_id: int):
    return db.query(Kategori).filter(Kategori.id == kategori_id).first()

def create_kategori(db: Session, kategori: KategoriCreate, kullanici_id: int):
    db_kategori = Kategori(**kategori.model_dump())
    db.add(db_kategori)
    db.commit()
    db.refresh(db_kategori)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Kategori Yönetimi",
        detay=f"Yeni kategori eklendi: {db_kategori.isim}"
    )
    db.add(log)
    db.commit()

    return db_kategori

def update_kategori(db: Session, kategori_id: int, kategori: KategoriUpdate, kullanici_id: int):
    db_kategori = db.query(Kategori).filter(Kategori.id == kategori_id).first()
    if not db_kategori:
        return None
    eski_isim = db_kategori.isim
    for key, value in kategori.model_dump(exclude_unset=True).items():
        setattr(db_kategori, key, value)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="UPDATE",
        modul="Kategori Yönetimi",
        detay=f"Kategori güncellendi. {eski_isim} -> {db_kategori.isim}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_kategori)
    return db_kategori

def delete_kategori(db: Session, kategori_id: int, kullanici_id: int):
    db_kategori = db.query(Kategori).filter(Kategori.id == kategori_id).first()
    if not db_kategori:
        return False
    db_kategori.aktif = False

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="DELETE",
        modul="Kategori Yönetimi",
        detay=f"Kategori silindi (pasife alındı): {db_kategori.isim}"
    )
    db.add(log)

    db.commit()
    return True
