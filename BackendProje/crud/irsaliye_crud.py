from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import datetime

from models import Irsaliye, Siparis, StokHareketi, SistemLog
from schemas import IrsaliyeCreate, IrsaliyeUpdate
from .stok_hareketi_crud import _fifo_palet_azalt


def generate_irsaliye_no(db: Session) -> str:
    """Otomatik irsaliye numarasi uret: IRS-2026-0001 formatinda"""
    bugun = datetime.utcnow()
    yil = bugun.year

    son_irsaliye = db.query(Irsaliye).filter(
        Irsaliye.irsaliye_no.startswith(f"IRS-{yil}-")
    ).order_by(Irsaliye.id.desc()).first()

    if son_irsaliye:
        try:
            son_no = int(son_irsaliye.irsaliye_no.split("-")[-1])
            yeni_no = son_no + 1
        except:
            yeni_no = 1
    else:
        yeni_no = 1

    return f"IRS-{yil}-{yeni_no:04d}"

def get_irsaliyeler(db: Session, skip: int = 0, limit: int = 100, durum: str = None, arama: str = None):
    query = db.query(Irsaliye).options(joinedload(Irsaliye.siparis))

    if durum:
        query = query.filter(Irsaliye.durum == durum)

    if arama:
        query = query.filter(
            or_(
                Irsaliye.irsaliye_no.ilike(f"%{arama}%"),
                Irsaliye.tir_plaka.ilike(f"%{arama}%")
            )
        )

    return query.order_by(Irsaliye.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

def get_irsaliye(db: Session, irsaliye_id: int):
    return db.query(Irsaliye).options(joinedload(Irsaliye.siparis)).filter(Irsaliye.id == irsaliye_id).first()

def create_irsaliye(db: Session, irsaliye_data: IrsaliyeCreate, kullanici_id: int):
    irsaliye_no = generate_irsaliye_no(db)

    db_irsaliye = Irsaliye(
        **irsaliye_data.model_dump(),
        irsaliye_no=irsaliye_no
    )
    db.add(db_irsaliye)
    db.flush()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="İrsaliye Yönetimi",
        detay=f"Yeni irsaliye oluşturuldu: {irsaliye_no}"
    )
    db.add(log)

    # Siparis kalemlerinden stok cikisi yap (sevkiyat plani henuz Yukleniyor olmadiysa)
    db_siparis = db.query(Siparis).options(
        joinedload(Siparis.kalemler),
        joinedload(Siparis.sevkiyat_plani)
    ).filter(Siparis.id == irsaliye_data.siparis_id).first()

    if db_siparis and db_siparis.kalemler:
        sevkiyat_stok_cikarildi = (
            db_siparis.sevkiyat_plani is not None and
            db_siparis.sevkiyat_plani.durum in ("Yukleniyor", "Yolda", "TeslimEdildi")
        )
        if not sevkiyat_stok_cikarildi:
            for kalem in db_siparis.kalemler:
                try:
                    _fifo_palet_azalt(db, kalem.urun_id, kalem.miktar)
                    db_stok = StokHareketi(
                        urun_id=kalem.urun_id,
                        hareket_tipi="cikis",
                        miktar=kalem.miktar,
                        siparis_no=db_siparis.siparis_no,
                        tir_plaka=db_irsaliye.tir_plaka,
                        aciklama=f"İrsaliye çıkışı - {irsaliye_no}",
                        kullanici_id=kullanici_id
                    )
                    db.add(db_stok)
                except ValueError as e:
                    hata_log = SistemLog(
                        kullanici_id=kullanici_id,
                        islem_tipi="ERROR",
                        modul="İrsaliye Yönetimi",
                        detay=f"Stok çıkışı hatası (Ürün ID: {kalem.urun_id}): {str(e)}"
                    )
                    db.add(hata_log)

    db.commit()
    db.refresh(db_irsaliye)
    return db_irsaliye

def update_irsaliye(db: Session, irsaliye_id: int, irsaliye_update: IrsaliyeUpdate, kullanici_id: int):
    db_irsaliye = db.query(Irsaliye).filter(Irsaliye.id == irsaliye_id).first()
    if not db_irsaliye:
        return None

    eski_durum = db_irsaliye.durum

    for key, value in irsaliye_update.model_dump(exclude_unset=True).items():
        setattr(db_irsaliye, key, value)

    if eski_durum != db_irsaliye.durum:
        log = SistemLog(
            kullanici_id=kullanici_id,
            islem_tipi="UPDATE",
            modul="İrsaliye Yönetimi",
            detay=f"İrsaliye durumu değiştirildi. Durum: {eski_durum} -> {db_irsaliye.durum}"
        )
        db.add(log)

    db.commit()
    db.refresh(db_irsaliye)
    return db_irsaliye
