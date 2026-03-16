from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import datetime

from models import Siparis, SiparisKalemi, SistemLog
from schemas import SiparisCreate, SiparisUpdate


def generate_siparis_no(db: Session) -> str:
    """Otomatik siparis numarasi uret: SIP-2026-0001 formatinda"""
    bugun = datetime.utcnow()
    yil = bugun.year

    son_siparis = db.query(Siparis).filter(
        Siparis.siparis_no.startswith(f"SIP-{yil}-")
    ).order_by(Siparis.id.desc()).first()

    if son_siparis:
        try:
            son_no = int(son_siparis.siparis_no.split("-")[-1])
            yeni_no = son_no + 1
        except:
            yeni_no = 1
    else:
        yeni_no = 1

    return f"SIP-{yil}-{yeni_no:04d}"

def get_siparisler(db: Session, skip: int = 0, limit: int = 100, durum: str = None, arama: str = None):
    query = db.query(Siparis).options(
        joinedload(Siparis.kalemler),
        joinedload(Siparis.olusturan_kullanici)
    )

    if durum:
        query = query.filter(Siparis.durum == durum)

    if arama:
        query = query.filter(
            or_(
                Siparis.siparis_no.ilike(f"%{arama}%"),
                Siparis.musteri_adi.ilike(f"%{arama}%")
            )
        )

    return query.order_by(Siparis.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

def get_siparis(db: Session, siparis_id: int):
    return db.query(Siparis).options(
        joinedload(Siparis.kalemler),
        joinedload(Siparis.olusturan_kullanici)
    ).filter(Siparis.id == siparis_id).first()

def create_siparis(db: Session, siparis: SiparisCreate, kullanici_id: int):
    siparis_no = generate_siparis_no(db)

    db_siparis = Siparis(
        **siparis.model_dump(exclude={"kalemler"}),
        siparis_no=siparis_no,
        olusturan_kullanici_id=kullanici_id
    )

    toplam_tutar = 0.0
    toplam_miktar = 0

    for kalem in siparis.kalemler:
        kalem_toplam = kalem.toplam or (kalem.miktar * kalem.birim_fiyat * (1 + kalem.kdv_orani / 100))

        kalem_dict = kalem.model_dump()
        kalem_dict['toplam'] = kalem_toplam

        db_kalem = SiparisKalemi(**kalem_dict)
        db_siparis.kalemler.append(db_kalem)
        toplam_tutar += kalem_toplam
        toplam_miktar += kalem.miktar

    db_siparis.top_miktar = toplam_miktar
    db_siparis.top_tutar = toplam_tutar

    db.add(db_siparis)
    db.flush()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Sipariş Yönetimi",
        detay=f"Yeni sipariş oluşturuldu: {siparis_no} - {db_siparis.musteri_adi}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_siparis)
    return db_siparis

def update_siparis(db: Session, siparis_id: int, siparis_update: SiparisUpdate, kullanici_id: int):
    db_siparis = db.query(Siparis).filter(Siparis.id == siparis_id).first()
    if not db_siparis:
        return None

    eski_durum = db_siparis.durum

    for key, value in siparis_update.model_dump(exclude_unset=True).items():
        setattr(db_siparis, key, value)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="UPDATE",
        modul="Sipariş Yönetimi",
        detay=f"Sipariş güncellendi: {db_siparis.siparis_no}. Durum: {eski_durum} -> {db_siparis.durum}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_siparis)
    return db_siparis

def delete_siparis(db: Session, siparis_id: int, kullanici_id: int):
    db_siparis = db.query(Siparis).filter(Siparis.id == siparis_id).first()
    if not db_siparis:
        return False

    db_siparis.aktif = False

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="DELETE",
        modul="Sipariş Yönetimi",
        detay=f"Sipariş silindi: {db_siparis.siparis_no}"
    )
    db.add(log)

    db.commit()
    return True
