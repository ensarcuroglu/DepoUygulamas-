from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, date

from database import Base


# ========================
# MARKA
# ========================

class Marka(Base):
    __tablename__ = "markalar"

    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(100), unique=True, nullable=False)
    aciklama = Column(Text, default="")
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişki
    urunler = relationship("Urun", back_populates="marka")


# ========================
# KATEGORİ
# ========================

class Kategori(Base):
    __tablename__ = "kategoriler"

    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(100), unique=True, nullable=False)
    aciklama = Column(Text, default="")
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişki
    urunler = relationship("Urun", back_populates="kategori")


# ========================
# DEPO
# ========================

class Depo(Base):
    __tablename__ = "depolar"

    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(100), unique=True, nullable=False)
    adres = Column(Text, default="")
    aciklama = Column(Text, default="")
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişki
    raflar = relationship("Raf", back_populates="depo")


# ========================
# RAF
# ========================

class Raf(Base):
    __tablename__ = "raflar"

    id = Column(Integer, primary_key=True, index=True)
    depo_id = Column(Integer, ForeignKey("depolar.id"), nullable=True)
    kod = Column(String(20), unique=True, nullable=False)       # Örn: "A-12", "B-04"
    bolge = Column(String(50), default="")                       # Örn: "Zemin Kat"
    kapasite = Column(Integer, default=100)
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    depo = relationship("Depo", back_populates="raflar")
    paletler = relationship("Palet", back_populates="raf")


# ========================
# TEDARİKÇİ
# ========================

class Tedarikci(Base):
    __tablename__ = "tedarikciler"

    id = Column(Integer, primary_key=True, index=True)
    firma_adi = Column(String(200), nullable=False, index=True)
    iletisim_kisi = Column(String(100), nullable=True)
    telefon = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    adres = Column(Text, nullable=True)
    vergi_no = Column(String(20), nullable=True)
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişki
    urunler = relationship("Urun", back_populates="tedarikci")


# ========================
# ÜRÜN
# ========================

class Urun(Base):
    __tablename__ = "urunler"

    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(200), nullable=False)
    marka_id = Column(Integer, ForeignKey("markalar.id"), nullable=True)
    kategori_id = Column(Integer, ForeignKey("kategoriler.id"), nullable=True)
    tedarikci_id = Column(Integer, ForeignKey("tedarikciler.id"), nullable=True)
    ean = Column(String(20), nullable=True)                      # EAN barkod
    barkod = Column(String(50), unique=True, nullable=True)      # Ek barkod/SKU
    ic_adet = Column(Integer, default=1)                         # Koli/paket başına iç adet
    gramaj = Column(Float, nullable=True)                        # Birim gramaj (kg)
    birim = Column(String(20), default="Adet")                   # Adet, Kg, Metre, Kutu
    fiyat = Column(Float, default=0.0)
    min_stok = Column(Integer, default=10)                       # Kritik stok seviyesi
    aciklama = Column(Text, default="")
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    marka = relationship("Marka", back_populates="urunler")
    kategori = relationship("Kategori", back_populates="urunler")
    tedarikci = relationship("Tedarikci", back_populates="urunler")
    lotlar = relationship("Lot", back_populates="urun")
    stok_hareketleri = relationship("StokHareketi", back_populates="urun")

    @property
    def durum(self):
        """Stok durumunu otomatik hesaplar"""
        miktar = self.stok_miktari
        if miktar <= 0:
            return "Stok Yok"
        elif miktar <= self.min_stok:
            return "Kritik Stok"
        else:
            return "Yeterli"


# ========================
# LOT / PARTİ TAKİBİ
# ========================

class Lot(Base):
    __tablename__ = "lotlar"

    id = Column(Integer, primary_key=True, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False)
    lot_no = Column(String(50), nullable=True, index=True)       # LOT numarası
    parti_no = Column(String(50), nullable=True)                  # Parti numarası
    uretim_tarihi = Column(Date, nullable=True)                   # Üretim tarihi
    son_kullanma_tarihi = Column(Date, nullable=True)             # SKT
    aciklama = Column(Text, default="")
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    urun = relationship("Urun", back_populates="lotlar")
    paletler = relationship("Palet", back_populates="lot")
    stok_hareketleri = relationship("StokHareketi", back_populates="lot")


# ========================
# PALET
# ========================

class Palet(Base):
    __tablename__ = "paletler"

    id = Column(Integer, primary_key=True, index=True)
    lot_id = Column(Integer, ForeignKey("lotlar.id"), nullable=False)
    raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)
    palet_no = Column(String(20), unique=True, nullable=False)   # Palet barkod numarası
    koli_adedi = Column(Integer, nullable=False)                  # Palet üstündeki koli sayısı
    palet_kg = Column(Float, nullable=True)                       # Toplam ağırlık (kg)
    vardiya = Column(String(20), nullable=True)                   # Vardiya bilgisi
    tarih = Column(DateTime, default=datetime.utcnow)             # Paletin oluşturulma tarihi
    aktif = Column(Boolean, default=True)                         # Depoda mı?
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    lot = relationship("Lot", back_populates="paletler")
    raf = relationship("Raf", back_populates="paletler")
    stok_hareketleri = relationship("StokHareketi", back_populates="palet")


# ========================
# STOK HAREKETİ
# ========================

class StokHareketi(Base):
    __tablename__ = "stok_hareketleri"

    id = Column(Integer, primary_key=True, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False)
    lot_id = Column(Integer, ForeignKey("lotlar.id"), nullable=True)
    palet_id = Column(Integer, ForeignKey("paletler.id"), nullable=True)
    raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)              # Ürün girişi için RAF
    hareket_tipi = Column(String(10), nullable=False)             # "giris" veya "cikis"
    miktar = Column(Integer, nullable=False)
    siparis_no = Column(String(100), nullable=True)               # Ürün çıkışı için Sipariş Numarası
    tir_plaka = Column(String(50), nullable=True)                 # Ürün çıkışı için Tır Plakası
    depo_kapi = Column(String(50), nullable=True)                 # Ürün çıkışı için Depo Kapısı
    barkodlar = Column(JSON, nullable=True)                       # Çoklu barkodları json array formatında saklamak için
    aciklama = Column(Text, default="")
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    tarih = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    urun = relationship("Urun", back_populates="stok_hareketleri")
    lot = relationship("Lot", back_populates="stok_hareketleri")
    palet = relationship("Palet", back_populates="stok_hareketleri")
    raf = relationship("Raf")   # Stok hareketinin bağlandığı raf
    kullanici = relationship("Kullanici", back_populates="stok_hareketleri")


# ========================
# SİSTEM LOGLARI
# ========================

class SistemLog(Base):
    __tablename__ = "sistem_loglari"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    islem_tipi = Column(String(50), nullable=False)               # örn: CREATE, UPDATE, DELETE
    modul = Column(String(50), nullable=False)                    # örn: Urunler, Kullanicilar, Stok
    detay = Column(Text, nullable=True)                           # örn: 'Fiyat 10 -> 20 yapıldı'
    eski_veri = Column(JSON, nullable=True)                       # json formatında eski hali
    yeni_veri = Column(JSON, nullable=True)                       # json formatında yeni hali
    tarih = Column(DateTime, default=datetime.utcnow)

    # İlişki
    kullanici = relationship("Kullanici")


# ========================
# KULLANICI
# ========================

class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_adi = Column(String(50), unique=True, nullable=False)
    sifre_hash = Column(String(255), nullable=False)
    ad_soyad = Column(String(100), nullable=False)
    rol = Column(String(20), default="depocu")                    # "admin", "depocu", "goruntuleyen", "lojistik"
    telefon = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    departman = Column(String(100), nullable=True)
    sicil_no = Column(String(50), nullable=True)
    kart_numarasi = Column(String(50), unique=True, nullable=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişki
    stok_hareketleri = relationship("StokHareketi", back_populates="kullanici")

from sqlalchemy import select, func
from sqlalchemy.orm import column_property

# N+1 Problemini çözmek için column_property ile veritabanı seviyesinde toplama yapıyoruz.
Urun.stok_miktari = column_property(
    select(func.coalesce(func.sum(Palet.koli_adedi), 0))
    .select_from(Lot)
    .join(Palet, Lot.id == Palet.lot_id)
    .where(Lot.urun_id == Urun.id)
    .where(Lot.aktif == True)
    .where(Palet.aktif == True)
    .correlate(Urun)
    .scalar_subquery()
)