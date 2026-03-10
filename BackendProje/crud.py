from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, or_
from datetime import datetime, timedelta, date
from fastapi.encoders import jsonable_encoder

from models import (
    Marka, Kategori, Depo, Raf, Tedarikci,
    Urun, Lot, Palet, StokHareketi, Kullanici, SistemLog, DestekTalebi,
    Siparis, SiparisKalemi, SevkiyatPlani, Irsaliye
)
from schemas import (
    MarkaCreate, MarkaUpdate,
    KategoriCreate, KategoriUpdate,
    DepoCreate, DepoUpdate,
    RafCreate, RafUpdate,
    TedarikciCreate, TedarikciUpdate,
    UrunCreate, UrunUpdate,
    LotCreate, LotUpdate,
    PaletCreate, PaletUpdate,
    StokHareketiCreate,
    DestekTalebiCreate, DestekTalebiUpdate,
    SiparisCreate, SiparisUpdate,
    SevkiyatPlaniCreate, SevkiyatPlaniUpdate,
    IrsaliyeCreate, IrsaliyeUpdate
)


# ========================
# MARKA CRUD
# ========================

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


# ========================
# KATEGORİ CRUD
# ========================

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


# ========================
# DEPO CRUD
# ========================

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
    db.commit()
    db.refresh(db_depo)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Depo Yönetimi",
        detay=f"Yeni depo eklendi: {db_depo.isim}"
    )
    db.add(log)
    db.commit()

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


# ========================
# RAF CRUD
# ========================

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


# ========================
# TEDARİKÇİ CRUD
# ========================

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


# ========================
# ÜRÜN CRUD
# ========================

def get_urunler(db: Session, skip: int = 0, limit: int = 50, search: str = None,
                kategori_id: int = None, marka_id: int = None, sadece_aktif: bool = True):
    query = db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori)
    )

    if sadece_aktif:
        query = query.filter(Urun.aktif == True)

    if search:
        query = query.filter(
            or_(
                Urun.isim.ilike(f"%{search}%"),
                Urun.barkod.ilike(f"%{search}%"),
                Urun.ean.ilike(f"%{search}%"),
                Urun.aciklama.ilike(f"%{search}%")
            )
        )

    if kategori_id:
        query = query.filter(Urun.kategori_id == kategori_id)

    if marka_id:
        query = query.filter(Urun.marka_id == marka_id)

    return query.offset(skip).limit(limit).all()

def get_urun(db: Session, urun_id: int):
    return db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori),
        joinedload(Urun.tedarikci)
    ).filter(Urun.id == urun_id).first()

def get_urun_by_barkod(db: Session, barkod: str):
    return db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori)
    ).filter(
        or_(Urun.barkod == barkod, Urun.ean == barkod)
    ).first()

def create_urun(db: Session, urun: UrunCreate, kullanici_id: int):
    db_urun = Urun(**urun.model_dump())
    db.add(db_urun)
    db.commit()
    db.refresh(db_urun)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Ürün Yönetimi",
        detay=f"Yeni ürün eklendi: {urun.isim} (Barkod: {urun.barkod or '-'})",
        yeni_veri=jsonable_encoder(urun.model_dump())
    )
    db.add(log)
    db.commit()

    return db_urun

def update_urun(db: Session, urun_id: int, urun: UrunUpdate, kullanici_id: int):
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        return None
    
    eski_veri = {c.name: getattr(db_urun, c.name) for c in db_urun.__table__.columns}

    for key, value in urun.model_dump(exclude_unset=True).items():
        setattr(db_urun, key, value)
    db_urun.guncelleme_tarihi = datetime.utcnow()
    db.commit()
    db.refresh(db_urun)

    yeni_veri = {c.name: getattr(db_urun, c.name) for c in db_urun.__table__.columns}
    # DateTime nesnelerini stringe çeviremeyebileceği için Pydantic model json üzerinden vermek daha iyi bir yaklaşım olabilir ama basit json dump işlemi için sadece id vb kullanmak pratik.
    
    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="UPDATE",
        modul="Ürün Yönetimi",
        detay=f"Ürün güncellendi: {db_urun.isim}",
        eski_veri=jsonable_encoder({"isim": eski_veri['isim'], "fiyat": eski_veri['fiyat'], "stok": db_urun.stok_miktari}),
        yeni_veri=jsonable_encoder({"isim": yeni_veri['isim'], "fiyat": yeni_veri['fiyat'], "stok": db_urun.stok_miktari})
    )
    db.add(log)
    db.commit()

    return db_urun

def delete_urun(db: Session, urun_id: int, kullanici_id: int):
    db_urun = db.query(Urun).filter(Urun.id == urun_id).first()
    if not db_urun:
        return False
    
    db_urun.aktif = False
    db_urun.guncelleme_tarihi = datetime.utcnow()

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="DELETE",
        modul="Ürün Yönetimi",
        detay=f"Ürün silindi (pasife alındı): {db_urun.isim}"
    )
    db.add(log)

    db.commit()
    return True

def get_kritik_urunler(db: Session):
    """Min stok seviyesinin altındaki ürünleri getirir"""
    return db.query(Urun).options(
        joinedload(Urun.marka),
        joinedload(Urun.kategori)
    ).filter(
        Urun.aktif == True,
        Urun.stok_miktari <= Urun.min_stok
    ).all()


# ========================
# LOT CRUD
# ========================

def get_lotlar(db: Session, skip: int = 0, limit: int = 50, urun_id: int = None, sadece_aktif: bool = True):
    query = db.query(Lot).options(joinedload(Lot.urun))
    if sadece_aktif:
        query = query.filter(Lot.aktif == True)
    if urun_id:
        query = query.filter(Lot.urun_id == urun_id)
    return query.order_by(Lot.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

def get_lot(db: Session, lot_id: int):
    return db.query(Lot).options(
        joinedload(Lot.urun),
        joinedload(Lot.paletler)
    ).filter(Lot.id == lot_id).first()

def get_lot_by_no(db: Session, lot_no: str):
    return db.query(Lot).options(
        joinedload(Lot.urun),
        joinedload(Lot.paletler)
    ).filter(Lot.lot_no == lot_no).first()

def create_lot(db: Session, lot: LotCreate):
    db_lot = Lot(**lot.model_dump())
    db.add(db_lot)
    db.commit()
    db.refresh(db_lot)
    return db_lot

def update_lot(db: Session, lot_id: int, lot: LotUpdate):
    db_lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not db_lot:
        return None
    for key, value in lot.model_dump(exclude_unset=True).items():
        setattr(db_lot, key, value)
    db.commit()
    db.refresh(db_lot)
    return db_lot

def delete_lot(db: Session, lot_id: int):
    db_lot = db.query(Lot).filter(Lot.id == lot_id).first()
    if not db_lot:
        return False
    db_lot.aktif = False
    db.commit()
    return True

def get_skt_yaklasan_lotlar(db: Session, gun: int = 30):
    """SKT'si belirtilen gün içinde dolacak lotları getirir"""
    sinir_tarih = date.today() + timedelta(days=gun)
    return db.query(Lot).options(
        joinedload(Lot.urun)
    ).filter(
        Lot.aktif == True,
        Lot.son_kullanma_tarihi != None,
        Lot.son_kullanma_tarihi <= sinir_tarih
    ).order_by(Lot.son_kullanma_tarihi.asc()).all()


# ========================
# PALET CRUD
# ========================

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
    """Paleti pasife alır (depodan çıkarır)"""
    db_palet = db.query(Palet).filter(Palet.id == palet_id).first()
    if not db_palet:
        return False
    db_palet.aktif = False
    db.commit()
    return True

def get_sonraki_palet_no(db: Session):
    """Bir sonraki palet numarasını üretir (1000001, 1000002, ...)"""
    son_palet = db.query(Palet).order_by(Palet.id.desc()).first()
    if son_palet and son_palet.palet_no.isdigit():
        return str(int(son_palet.palet_no) + 1)
    return "1000001"


# ========================
# STOK HAREKETİ CRUD
# ========================

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

def create_stok_hareketi(db: Session, hareket: StokHareketiCreate, kullanici_id: int = None):
    """Stok hareketi oluşturur ve arka planda Palet bakiyelerini günceller."""
    
    # 1. Ürünü bul
    db_urun = db.query(Urun).filter(Urun.id == hareket.urun_id).first()
    if not db_urun:
        raise ValueError("Ürün bulunamadı")
        
    urun_ismi = db_urun.isim

    # ==========================
    # ÇIKIŞ İŞLEMİ (FIFO MANTIĞI)
    # ==========================
    if hareket.hareket_tipi == "cikis":
        if hareket.miktar > db_urun.stok_miktari:
            raise ValueError(f"Yetersiz stok! Mevcut: {db_urun.stok_miktari}, İstenen: {hareket.miktar}")
            
        kalan_dusulecek_miktar = hareket.miktar
        
        # Ürüne ait aktif paletleri SKT'ye veya Üretim Tarihine (Lot üzerinden) göre sırala (FIFO)
        aktif_paletler = db.query(Palet).join(Lot).filter(
            Lot.urun_id == hareket.urun_id,
            Lot.aktif == True,
            Palet.aktif == True,
            Palet.koli_adedi > 0
        ).order_by(
            Lot.son_kullanma_tarihi.asc().nulls_last(), # Önce SKT'si yakın olanlar
            Lot.uretim_tarihi.asc().nulls_last(),       # Sonra eski üretimliler
            Palet.tarih.asc()                           # En son palet oluşturma tarihi
        ).all()
        
        for palet in aktif_paletler:
            if kalan_dusulecek_miktar <= 0:
                break
                
            if palet.koli_adedi <= kalan_dusulecek_miktar:
                # Paletin tamamı çıkışa gidiyor, palet kapanır
                kalan_dusulecek_miktar -= palet.koli_adedi
                palet.koli_adedi = 0
                palet.aktif = False
            else:
                # Paletin sadece bir kısmı çıkıyor
                palet.koli_adedi -= kalan_dusulecek_miktar
                kalan_dusulecek_miktar = 0
                
        if kalan_dusulecek_miktar > 0:
            # Buraya normal şartlarda düşmemeli yukarıda stok kontrolü yapıldı ama her ihtimale karşı
            raise ValueError("Sistemde yeterli koli bulunamadı (Veri uyuşmazlığı)")
            
        # İstek olarak palet_id geldiyse, sadece ilişkilendirmek için (geriye dönük uyum)
        if hareket.palet_id:
            pass # Eski mantıkta tüm paleti kapatıyordu, artık koli bazlı düşüyoruz.

    # ==========================
    # GİRİŞ İŞLEMİ
    # ==========================
    elif hareket.hareket_tipi == "giris":
        # Otomatik bir LOT bul veya oluştur
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
            db.flush() # ID almak için
            
        hareket.lot_id = db_lot.id
        
        # Otomatik bir PALET oluştur ve stok miktarını buraya ekle
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

    # 4. Stok Logu Gönder
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


# ========================
# DASHBOARD İSTATİSTİKLERİ
# ========================

def get_dashboard_stats(db: Session):
    toplam_urun = db.query(func.count(Urun.id)).filter(Urun.aktif == True).scalar()

    # Kritik stok: SQL sorgusu ile hesaplanır
    kritik_stok = db.query(func.count(Urun.id)).filter(
        Urun.aktif == True,
        Urun.stok_miktari <= Urun.min_stok
    ).scalar()

    bugun = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    bugunku_hareket = db.query(func.count(StokHareketi.id)).filter(
        StokHareketi.tarih >= bugun
    ).scalar()

    # Toplam değer: SQL fonksiyonu ile sum(fiyat * stok) hesaplanır
    toplam_deger = db.query(func.coalesce(func.sum(Urun.stok_miktari * Urun.fiyat), 0.0)).filter(Urun.aktif == True).scalar()

    return {
        "toplam_urun": toplam_urun,
        "kritik_stok_sayisi": kritik_stok,
        "bugunku_hareket": bugunku_hareket,
        "toplam_deger": round(toplam_deger, 2)
    }


# ========================
# DESTEK MASASI CRUD
# ========================

def get_destek_talepleri(db: Session, skip: int = 0, limit: int = 100, kullanici_id: int = None, durum: str = None):
    query = db.query(DestekTalebi).options(joinedload(DestekTalebi.kullanici))
    if kullanici_id:
        query = query.filter(DestekTalebi.kullanici_id == kullanici_id)
    if durum:
        query = query.filter(DestekTalebi.durum == durum)
    return query.order_by(DestekTalebi.olusturma_tarihi.desc()).offset(skip).limit(limit).all()

def get_destek_talebi(db: Session, talep_id: int):
    return db.query(DestekTalebi).options(joinedload(DestekTalebi.kullanici)).filter(DestekTalebi.id == talep_id).first()

def create_destek_talebi(db: Session, talep: DestekTalebiCreate, kullanici_id: int):
    db_talep = DestekTalebi(**talep.model_dump(), kullanici_id=kullanici_id)
    db.add(db_talep)
    db.commit()
    db.refresh(db_talep)

    log = SistemLog(
        kullanici_id=kullanici_id,
        islem_tipi="CREATE",
        modul="Destek Masası",
        detay=f"Yeni destek talebi oluşturuldu: {db_talep.konu}"
    )
    db.add(log)
    db.commit()

    return db_talep

def update_destek_talebi(db: Session, talep_id: int, talep_update: DestekTalebiUpdate, admin_id: int):
    db_talep = db.query(DestekTalebi).filter(DestekTalebi.id == talep_id).first()
    if not db_talep:
        return None

    eski_durum = db_talep.durum

    for key, value in talep_update.model_dump(exclude_unset=True).items():
        setattr(db_talep, key, value)

    db_talep.guncelleme_tarihi = datetime.utcnow()

    log = SistemLog(
        kullanici_id=admin_id,
        islem_tipi="UPDATE",
        modul="Destek Masası",
        detay=f"Destek talebi güncellendi (#{db_talep.id}). Durum: {eski_durum} -> {db_talep.durum}"
    )
    db.add(log)

    db.commit()
    db.refresh(db_talep)
    return db_talep


# ========================
# SİPARİŞ CRUD
# ========================

def generate_siparis_no(db: Session) -> str:
    """Otomatik sipariş numarası üret: SIP-2026-0001 formatında"""
    bugun = datetime.utcnow()
    yil = bugun.year

    # Bu yıla ait son sipariş numarasını bul
    son_siparis = db.query(Siparis).filter(
        Siparis.siparis_no.startswith(f"SIP-{yil}-")
    ).order_by(Siparis.id.desc()).first()

    if son_siparis:
        # Son numaradan sıra numarası çıkar
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
    # Otomatik sipariş numarası
    siparis_no = generate_siparis_no(db)

    # Sipariş oluştur
    db_siparis = Siparis(
        **siparis.model_dump(exclude={"kalemler"}),
        siparis_no=siparis_no,
        olusturan_kullanici_id=kullanici_id
    )

    # Kalemler ekle
    toplam_tutar = 0.0
    toplam_miktar = 0

    for kalem in siparis.kalemler:
        # Toplam hesapla (gönderilmediyse)
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

    # Sistem logu
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


# ========================
# SEVKİYAT PLANI CRUD
# ========================

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
    db_plan = db.query(SevkiyatPlani).filter(SevkiyatPlani.id == plan_id).first()
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


# ========================
# İRSALİYE CRUD
# ========================

def generate_irsaliye_no(db: Session) -> str:
    """Otomatik irsaliye numarası üret: IRS-2026-0001 formatında"""
    bugun = datetime.utcnow()
    yil = bugun.year

    # Bu yıla ait son irsaliye numarasını bul
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
    # Otomatik irsaliye numarası
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
