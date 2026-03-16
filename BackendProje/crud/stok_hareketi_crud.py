from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from models import StokHareketi, Urun, Lot, Palet, SistemLog
from schemas import StokHareketiCreate
from core.api_exceptions import KayitBulunamadiError, YetersizStokError, StokVeriUyumsuzluguError


def get_stok_hareketleri(db: Session, skip: int = 0, limit: int = 50, urun_id: int = None, lot_id: int = None, hareket_tipi: str = None):
    query = db.query(StokHareketi).options(
        joinedload(StokHareketi.kullanici),
        joinedload(StokHareketi.raf)
    ).order_by(StokHareketi.tarih.desc())
    if urun_id:
        query = query.filter(StokHareketi.urun_id == urun_id)
    if lot_id:
        query = query.filter(StokHareketi.lot_id == lot_id)
    if hareket_tipi:
        query = query.filter(StokHareketi.hareket_tipi == hareket_tipi)
    return query.offset(skip).limit(limit).all()

def _fifo_palet_azalt(db: Session, urun_id: int, miktar: int):
    """FIFO mantigi ile palet stoklarini duser. DB commit yapmaz — cagiran fonksiyon commit eder.

    SELECT FOR UPDATE ile paletler kilitlenir; eşzamanlı çıkış istekleri
    sıralanarak race condition engellenir.
    """
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        raise KayitBulunamadiError("Ürün", urun_id)

    if miktar > db_urun.stok_miktari:
        raise YetersizStokError(db_urun.isim, db_urun.stok_miktari, miktar)

    kalan = miktar
    aktif_paletler = db.query(Palet).join(Lot).filter(
        Lot.urun_id == urun_id,
        Lot.aktif == True,
        Palet.aktif == True,
        Palet.koli_adedi > 0
    ).order_by(
        Lot.son_kullanma_tarihi.asc().nulls_last(),
        Lot.uretim_tarihi.asc().nulls_last(),
        Palet.tarih.asc()
    ).with_for_update().all()

    for palet in aktif_paletler:
        if kalan <= 0:
            break
        if palet.koli_adedi <= kalan:
            kalan -= palet.koli_adedi
            palet.koli_adedi = 0
            palet.aktif = False
        else:
            palet.koli_adedi -= kalan
            kalan = 0

    if kalan > 0:
        raise StokVeriUyumsuzluguError(db_urun.isim)


def create_stok_hareketi(db: Session, hareket: StokHareketiCreate, kullanici_id: int = None):
    """Stok hareketi olusturur ve arka planda Palet bakiyelerini gunceller."""

    # 1. Urunu bul
    db_urun = db.query(Urun).filter(Urun.id == hareket.urun_id).first()
    if not db_urun:
        raise KayitBulunamadiError("Ürün", hareket.urun_id)

    urun_ismi = db_urun.isim

    # ==========================
    # CIKIS ISLEMI (FIFO MANTIGI)
    # ==========================
    if hareket.hareket_tipi == "cikis":
        _fifo_palet_azalt(db, hareket.urun_id, hareket.miktar)

        if hareket.palet_id:
            pass  # Eski mantikte tum paleti kapatiyordu, artik koli bazli dusuyoruz.

    # ==========================
    # GIRIS ISLEMI
    # ==========================
    elif hareket.hareket_tipi == "giris":
        otomatik_lot_no = "OTOMATIK-GIRIS"
        db_lot = db.query(Lot).filter(
            Lot.urun_id == hareket.urun_id,
            Lot.lot_no == otomatik_lot_no,
            Lot.aktif == True
        ).first()

        if not db_lot:
            db_lot = Lot(
                urun_id=hareket.urun_id,
                lot_no=otomatik_lot_no,
                aciklama="Hızlı Giriş ekranından oluşturulan varsayılan lot"
            )
            db.add(db_lot)
            db.flush()

        hareket.lot_id = db_lot.id

        yeni_palet_no = f"OTM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        db_palet = Palet(
            lot_id=db_lot.id,
            raf_id=hareket.raf_id,
            palet_no=yeni_palet_no,
            koli_adedi=hareket.miktar,
            vardiya="Hızlı Giriş"
        )
        db.add(db_palet)
        db.flush()
        hareket.palet_id = db_palet.id

    # 3. Stok Hareketini Kaydet
    db_hareket = StokHareketi(
        **hareket.model_dump(),
        kullanici_id=kullanici_id
    )
    db.add(db_hareket)

    # 4. Stok Logu Gonder
    islem_turu_metni = "Giriş Yapıldı" if hareket.hareket_tipi == "giris" else "Çıkış Yapıldı"
    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="UPDATE",
        modul="Stok İşlemleri",
        detay=f"Stok {islem_turu_metni}: {urun_ismi} | miktar: {hareket.miktar}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_hareket)
    return db_hareket
