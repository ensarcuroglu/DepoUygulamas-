from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from database import Base


class Kategori(Base):
    __tablename__ = "kategoriler"

    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(100), unique=True, nullable=False)
    aciklama = Column(Text, default="")

    # İlişki: Bir kategoride birden fazla ürün olabilir
    urunler = relationship("Urun", back_populates="kategori")


class Raf(Base):
    __tablename__ = "raflar"

    id = Column(Integer, primary_key=True, index=True)
    kod = Column(String(20), unique=True, nullable=False)   # Örn: "A-12", "B-04"
    bolge = Column(String(50), default="")                   # Örn: "Depo-1", "Zemin Kat"
    kapasite = Column(Integer, default=100)

    # İlişki
    urunler = relationship("Urun", back_populates="raf")


class Urun(Base):
    __tablename__ = "urunler"

    id = Column(Integer, primary_key=True, index=True)
    isim = Column(String(200), nullable=False)
    barkod = Column(String(50), unique=True, nullable=True)
    aciklama = Column(Text, default="")
    kategori_id = Column(Integer, ForeignKey("kategoriler.id"), nullable=True)
    raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)
    stok_miktari = Column(Integer, default=0)
    min_stok = Column(Integer, default=10)                    # Bu seviyenin altı = Kritik Stok
    birim = Column(String(20), default="Adet")               # Adet, Kg, Metre, Kutu...
    fiyat = Column(Float, default=0.0)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    kategori = relationship("Kategori", back_populates="urunler")
    raf = relationship("Raf", back_populates="urunler")
    stok_hareketleri = relationship("StokHareketi", back_populates="urun")

    @property
    def durum(self):
        """Stok durumunu otomatik hesaplar"""
        if self.stok_miktari <= 0:
            return "Stok Yok"
        elif self.stok_miktari <= self.min_stok:
            return "Kritik Stok"
        else:
            return "Yeterli"


class StokHareketi(Base):
    __tablename__ = "stok_hareketleri"

    id = Column(Integer, primary_key=True, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False)
    hareket_tipi = Column(String(10), nullable=False)        # "giris" veya "cikis"
    miktar = Column(Integer, nullable=False)
    aciklama = Column(Text, default="")
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    tarih = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    urun = relationship("Urun", back_populates="stok_hareketleri")
    kullanici = relationship("Kullanici", back_populates="stok_hareketleri")


class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_adi = Column(String(50), unique=True, nullable=False)
    sifre_hash = Column(String(255), nullable=False)
    ad_soyad = Column(String(100), nullable=False)
    rol = Column(String(20), default="depocu")               # "admin", "depocu", "goruntuleyen"
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişki
    stok_hareketleri = relationship("StokHareketi", back_populates="kullanici")

class Tedarikci(Base):
    __tablename__ = "tedarikciler"

    id = Column(Integer, primary_key=True, index=True)
    firma_adi = Column(String(200), index=True)
    iletisim_kisi = Column(String(100), nullable=True)
    telefon = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)