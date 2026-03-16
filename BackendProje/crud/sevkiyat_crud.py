from sqlalchemy.orm import Session, joinedload
from datetime import date

from models import SevkiyatPlani, Siparis, StokHareketi, SistemLog
from schemas import SevkiyatPlaniCreate, SevkiyatPlaniUpdate
from core.api_exceptions import APIException
from .stok_hareketi_crud import _fifo_palet_azalt


def get_sevkiyat_planlari(db: Session, skip: int = 0, limit: int = 100, durum: str = None, tarih_baslang: date = None, tarih_bitis: date = None):
    query = db.query(SevkiyatPlani).options(joinedload(SevkiyatPlani.siparis))

    if durum:
        query = query.filter(SevkiyatPlani.durum == durum)

    if tarih_baslang:
        query = query.filter(SevkiyatPlani.yukleme_tarihi >= tarih_baslang)

    if tarih_bitis:
        query = query.filter(SevkiyatPlani.yukleme_tarihi <= tarih_bitis)

    return query.order_by(SevkiyatPlani.yukleme_tarihi.desc()).offset(skip).limit(limit).all()

def get_sevkiyat_plani(db: Session, plan_id: int):
    return db.query(SevkiyatPlani).options(joinedload(SevkiyatPlani.siparis)).filter(SevkiyatPlani.id == plan_id).first()

def create_sevkiyat_plani(db: Session, plan: SevkiyatPlaniCreate, kullanici_id: int):
    db_plan = SevkiyatPlani(**plan.model_dump())
    db.add(db_plan)
    db.flush()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Sevkiyat Planlama",
        detay=f"Yeni sevkiyat planı oluşturuldu - Sipariş ID: {plan.siparis_id}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_plan)
    return db_plan

def update_sevkiyat_plani(db: Session, plan_id: int, plan_update: SevkiyatPlaniUpdate, kullanici_id: int):
    db_plan = db.query(SevkiyatPlani).options(joinedload(SevkiyatPlani.siparis).joinedload(Siparis.kalemler)).filter(SevkiyatPlani.id == plan_id).first()
    if not db_plan:
        return None

    eski_durum = db_plan.durum

    for key, value in plan_update.model_dump(exclude_unset=True).items():
        setattr(db_plan, key, value)

    if eski_durum != db_plan.durum:
        log = SistemLog(
            kullanici_id=kullanici_id,
            islem_tipi="UPDATE",
            modul="Sevkiyat Planlama",
            detay=f"Sevkiyat planı durumu değiştirildi. Durum: {eski_durum} -> {db_plan.durum}"
        )
        db.add(log)

        # Durum "Yukleniyor"a gecince siparis kalemlerinden otomatik stok cikisi yap (FIFO)
        if db_plan.durum == "Yukleniyor" and eski_durum not in ("Yukleniyor", "Yolda", "TeslimEdildi"):
            db_siparis = db_plan.siparis
            if db_siparis and db_siparis.kalemler:
                for kalem in db_siparis.kalemler:
                    try:
                        _fifo_palet_azalt(db, kalem.urun_id, kalem.miktar)
                        db_stok = StokHareketi(
                            urun_id=kalem.urun_id,
                            hareket_tipi="cikis",
                            miktar=kalem.miktar,
                            siparis_no=db_siparis.siparis_no,
                            tir_plaka=db_plan.tir_plaka,
                            depo_kapi=db_plan.depo_kapi,
                            aciklama=f"Sevkiyat yüklemesi - {db_siparis.siparis_no}",
                            kullanici_id=kullanici_id
                        )
                        db.add(db_stok)
                    except APIException as e:
                        hata_log = SistemLog(
                            kullanici_id=kullanici_id,
                            islem_tipi="ERROR",
                            modul="Sevkiyat Planlama",
                            detay=f"Stok çıkışı hatası (Ürün ID: {kalem.urun_id}): {str(e)}"
                        )
                        db.add(hata_log)

    db.commit()
    db.refresh(db_plan)
    return db_plan

def delete_sevkiyat_plani(db: Session, plan_id: int, kullanici_id: int):
    db_plan = db.query(SevkiyatPlani).filter(SevkiyatPlani.id == plan_id).first()
    if not db_plan:
        return False

    db.delete(db_plan)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="DELETE",
        modul="Sevkiyat Planlama",
        detay=f"Sevkiyat planı silindi - Sipariş ID: {db_plan.siparis_id}"
    )
    db.add(log)

    db.commit()
    return True
