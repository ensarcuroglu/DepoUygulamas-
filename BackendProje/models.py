from typing import Optional
from sqlalchemy import (
    String,
    Float,
    DateTime,
    Date,
    ForeignKey,
    Text,
    Boolean,
    JSON,
    Integer,
    Index,
    UniqueConstraint,
    PrimaryKeyConstraint,
    func,
    select,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date, datetime

from database import Base


# ========================
# MARKA
# ========================

class Marka(Base):
    __tablename__ = "markalar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    isim: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, default="")
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişki
    urunler: Mapped[list["Urun"]] = relationship("Urun", back_populates="marka")


# ========================
# KATEGORİ
# ========================

class Kategori(Base):
    __tablename__ = "kategoriler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    isim: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    ikon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="FolderOpen")
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişki
    urunler: Mapped[list["Urun"]] = relationship("Urun", back_populates="kategori")


# ========================
# DEPO
# ========================

class Depo(Base):
    __tablename__ = "depolar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    isim: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    adres: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişki
    zonlar: Mapped[list["Zon"]] = relationship("Zon", back_populates="depo")
    raflar: Mapped[list["Raf"]] = relationship("Raf", back_populates="depo")


# ========================
# ZON
# ========================

class Zon(Base):
    __tablename__ = "zonlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    depo_id: Mapped[int] = mapped_column(Integer, ForeignKey("depolar.id"), nullable=False)
    isim: Mapped[str] = mapped_column(String(100), nullable=False)
    tip: Mapped[str] = mapped_column(String(30), nullable=False)
    kod: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    aciklama: Mapped[str] = mapped_column(Text, default="")
    sira: Mapped[int] = mapped_column(Integer, default=0)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # Iliski
    depo: Mapped["Depo"] = relationship("Depo", back_populates="zonlar")
    raflar: Mapped[list["Raf"]] = relationship("Raf", back_populates="zon")


# ========================
# RAF
# ========================

class Raf(Base):
    __tablename__ = "raflar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    depo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("depolar.id"), nullable=True)
    zon_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("zonlar.id"), nullable=True)
    kod: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    bolge: Mapped[str] = mapped_column(String(50), default="")
    kapasite: Mapped[int] = mapped_column(Integer, default=100)
    max_agirlik_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    koridor: Mapped[str] = mapped_column(String(10), default="")
    kat: Mapped[int] = mapped_column(Integer, default=0)
    goz: Mapped[int] = mapped_column(Integer, default=0)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    is_staging: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişkiler
    depo: Mapped["Depo"] = relationship("Depo", back_populates="raflar")
    zon: Mapped["Zon"] = relationship("Zon", back_populates="raflar")
    paletler: Mapped[list["Palet"]] = relationship("Palet", back_populates="raf")


# ========================
# TEDARİKÇİ
# ========================

class Tedarikci(Base):
    __tablename__ = "tedarikciler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    firma_adi: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    iletisim_kisi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    telefon: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    adres: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vergi_no: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişki
    urunler: Mapped[list["Urun"]] = relationship("Urun", back_populates="tedarikci")


# ========================
# ÜRÜN
# ========================

class Urun(Base):
    __tablename__ = "urunler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    isim: Mapped[str] = mapped_column(String(200), nullable=False)
    marka_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("markalar.id"), nullable=True)
    kategori_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("kategoriler.id"), nullable=True)
    tedarikci_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tedarikciler.id"), nullable=True)
    ean: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    barkod: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    ic_adet: Mapped[int] = mapped_column(Integer, default=1)
    gramaj: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    birim: Mapped[str] = mapped_column(String(20), default="Adet")
    fiyat: Mapped[float] = mapped_column(Float, default=0.0)
    min_stok: Mapped[int] = mapped_column(Integer, default=10)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    depolama_tipi: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="Kuru")
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
    )

    # İlişkiler
    marka: Mapped[Optional["Marka"]] = relationship("Marka", back_populates="urunler")
    kategori: Mapped[Optional["Kategori"]] = relationship("Kategori", back_populates="urunler")
    tedarikci: Mapped[Optional["Tedarikci"]] = relationship("Tedarikci", back_populates="urunler")
    lotlar: Mapped[list["Lot"]] = relationship("Lot", back_populates="urun")
    stok_hareketleri: Mapped[list["StokHareketi"]] = relationship("StokHareketi", back_populates="urun")

    @property
    def durum(self) -> str:
        miktar = getattr(self, "stok_miktari", 0) or 0
        if miktar <= 0:
            return "Stok Yok"
        elif miktar <= self.min_stok:
            return "Kritik Stok"
        return "Yeterli"


# ========================
# LOT / PARTİ TAKİBİ
# ========================

class Lot(Base):
    __tablename__ = "lotlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    urun_id: Mapped[int] = mapped_column(Integer, ForeignKey("urunler.id"), nullable=False)
    lot_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    parti_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    uretim_tarihi: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    son_kullanma_tarihi: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="")
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişkiler
    urun: Mapped["Urun"] = relationship("Urun", back_populates="lotlar")
    paletler: Mapped[list["Palet"]] = relationship("Palet", back_populates="lot")
    stok_hareketleri: Mapped[list["StokHareketi"]] = relationship("StokHareketi", back_populates="lot")


# ========================
# PALET
# ========================

class Palet(Base):
    __tablename__ = "paletler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lotlar.id"), nullable=False)
    raf_id: Mapped[int] = mapped_column(Integer, ForeignKey("raflar.id"), nullable=False)
    palet_no: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    koli_adedi: Mapped[int] = mapped_column(Integer, nullable=False)
    palet_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    vardiya: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tarih: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # ── Üretim paleti alanları ──
    kaynak: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    durum: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    uretim_tarihi: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    lot_no: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    # ── Kabul audit alanları ──
    kabul_eden_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    kabul_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    iptal_sebebi: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ── Üretim meta alanları ──
    uretim_hatti: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    makine_kodu: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    operator_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    brut_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    net_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # İlişkiler
    lot: Mapped["Lot"] = relationship("Lot", back_populates="paletler")
    raf: Mapped["Raf"] = relationship("Raf", back_populates="paletler")
    stok_hareketleri: Mapped[list["StokHareketi"]] = relationship(
        "StokHareketi", back_populates="palet")
    kabul_eden_kullanici: Mapped[Optional["Kullanici"]] = relationship(
    "Kullanici",
    foreign_keys=[kabul_eden_kullanici_id],
    )


# ========================
# ÜRETİM SERİ SAYACI
# ========================

class UretimSeriSayac(Base):
    __tablename__ = "uretim_seri_sayac"
    __table_args__ = (
        PrimaryKeyConstraint("prefix", "tarih"),
    )

    prefix: Mapped[str] = mapped_column(String(10), default="PRD", nullable=False)
    tarih: Mapped[date] = mapped_column(Date, nullable=False)
    son_seri_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# ========================
# PALET DURUM LOGU
# ========================

class PaletDurumLog(Base):
    __tablename__ = "palet_durum_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    palet_id: Mapped[int] = mapped_column(Integer, ForeignKey("paletler.id"), nullable=False)
    eski_durum: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    yeni_durum: Mapped[str] = mapped_column(String(30), nullable=False)
    degistiren_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    degisim_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sebep: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    palet: Mapped["Palet"] = relationship("Palet", foreign_keys=[palet_id])
    degistiren_kullanici: Mapped[Optional["Kullanici"]] = relationship(
        "Kullanici",
        foreign_keys=[degistiren_kullanici_id],
    )


# ========================
# STOK HAREKETİ
# ========================

class StokHareketi(Base):
    __tablename__ = "stok_hareketleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    urun_id: Mapped[int] = mapped_column(Integer, ForeignKey("urunler.id"), nullable=False)
    lot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("lotlar.id"), nullable=True)
    palet_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("paletler.id"), nullable=True)
    raf_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("raflar.id"), nullable=True)
    hareket_tipi: Mapped[str] = mapped_column(String(10), nullable=False)
    miktar: Mapped[int] = mapped_column(Integer, nullable=False)
    siparis_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    irsaliye_no: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tir_plaka: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    depo_kapi: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    barkodlar: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    sofor_adi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tasiyici_firma: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    aciklama: Mapped[str] = mapped_column(Text, default="", nullable=False)
    kullanici_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    tarih: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişkiler
    urun: Mapped["Urun"] = relationship("Urun", back_populates="stok_hareketleri")
    lot: Mapped[Optional["Lot"]] = relationship("Lot", back_populates="stok_hareketleri")
    palet: Mapped[Optional["Palet"]] = relationship("Palet", back_populates="stok_hareketleri")
    raf: Mapped[Optional["Raf"]] = relationship("Raf")
    kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici", back_populates="stok_hareketleri")


# ========================
# SİSTEM LOGLARI
# ========================

class SistemLog(Base):
    __tablename__ = "sistem_loglari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kullanici_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    islem_tipi: Mapped[str] = mapped_column(String(50), nullable=False)
    modul: Mapped[str] = mapped_column(String(50), nullable=False)
    detay: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    eski_veri: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    yeni_veri: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    tarih: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişki
    kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici")


# ========================
# KULLANICI
# ========================

class Kullanici(Base):
    __tablename__ = "kullanicilar"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    kullanici_adi: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    sifre_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ad_soyad: Mapped[str] = mapped_column(String(100), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), default="depocu")
    
    telefon: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    departman: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sicil_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    kart_numarasi: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)
    
    depo_id: Mapped[Optional[int]] = mapped_column(ForeignKey("depolar.id"), nullable=True)
    depo_erisimi_yok: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    refresh_token_son_kullanim: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    olusturma_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)

    # İlişkiler (Relationship yapısı eski halinde kalabilir, Pyright bunu çözer)
    stok_hareketleri: Mapped[list["StokHareketi"]] = relationship(
    "StokHareketi",
    back_populates="kullanici",
    )
    destek_talepleri: Mapped[list["DestekTalebi"]] = relationship(
        "DestekTalebi",
        back_populates="kullanici",
    )
    depo: Mapped[Optional["Depo"]] = relationship(
        "Depo",
        foreign_keys=[depo_id],
    )


# ========================
# DESTEK MASASI
# ========================

class DestekTalebi(Base):
    __tablename__ = "destek_talepleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kullanici_id: Mapped[int] = mapped_column(Integer, ForeignKey("kullanicilar.id"), nullable=False)
    konu: Mapped[str] = mapped_column(String(200), nullable=False)
    kategori: Mapped[str] = mapped_column(String(50), nullable=False)
    oncelik: Mapped[str] = mapped_column(String(20), default="Normal")
    durum: Mapped[str] = mapped_column(String(20), default="Açık")
    aciklama: Mapped[str] = mapped_column(Text, nullable=False)
    admin_cevabi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
    )    

    # İlişki
    kullanici: Mapped["Kullanici"] = relationship("Kullanici", back_populates="destek_talepleri")

# ========================
# SİPARİŞ
# ========================

class Siparis(Base):
    __tablename__ = "siparisler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    siparis_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    musteri_adi: Mapped[str] = mapped_column(String(200), nullable=False)
    teslimat_adresi: Mapped[str] = mapped_column(Text, nullable=False)
    teslimat_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    durum: Mapped[str] = mapped_column(String(20), default="Bekleme")
    top_miktar: Mapped[int] = mapped_column(Integer, default=0)
    top_tutar: Mapped[float] = mapped_column(Float, default=0.0)
    notlar: Mapped[str] = mapped_column(Text, default="")
    olusturan_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
    )
    aktif: Mapped[bool] = mapped_column(Boolean, default=True)

    # İlişkiler
    kalemler: Mapped[list["SiparisKalemi"]] = relationship(
        "SiparisKalemi", back_populates="siparis", cascade="all, delete-orphan"
    )
    sevkiyat_plani: Mapped[Optional["SevkiyatPlani"]] = relationship(
        "SevkiyatPlani", back_populates="siparis", uselist=False
    )
    irsaliyeler: Mapped[list["Irsaliye"]] = relationship("Irsaliye", back_populates="siparis")
    olusturan_kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici")


# ========================
# SİPARİŞ KALEMİ
# ========================

class SiparisKalemi(Base):
    __tablename__ = "siparis_kalemleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    siparis_id: Mapped[int] = mapped_column(Integer, ForeignKey("siparisler.id"), nullable=False)
    urun_id: Mapped[int] = mapped_column(Integer, ForeignKey("urunler.id"), nullable=False)
    miktar: Mapped[int] = mapped_column(Integer, nullable=False)
    birim_fiyat: Mapped[float] = mapped_column(Float, nullable=False)
    kdv_orani: Mapped[float] = mapped_column(Float, default=18.0)
    toplam: Mapped[float] = mapped_column(Float, nullable=False)

    # İlişkiler
    siparis: Mapped["Siparis"] = relationship("Siparis", back_populates="kalemler")
    urun: Mapped["Urun"] = relationship("Urun")


# ========================
# SEVKİYAT PLANI
# ========================

class SevkiyatPlani(Base):
    __tablename__ = "sevkiyat_planlari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    siparis_id: Mapped[int] = mapped_column(Integer, ForeignKey("siparisler.id"), unique=True, nullable=False)
    tir_plaka: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sofor_adi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sofor_telefon: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    depo_kapi: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    yukleme_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    cikis_saati: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    varis_saati: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Planlandi")
    notlar: Mapped[str] = mapped_column(Text, default="")
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
)

    # İlişkiler
    siparis: Mapped["Siparis"] = relationship("Siparis", back_populates="sevkiyat_plani")
    kalemler: Mapped[list["SevkiyatKalemi"]] = relationship(
        "SevkiyatKalemi", back_populates="sevkiyat",
        cascade="all, delete-orphan",
    )


# ========================
# SEVKİYAT KALEMİ
# ========================

class SevkiyatKalemi(Base):
    __tablename__ = "sevkiyat_kalemleri"
    __table_args__ = (
        UniqueConstraint(
            "sevkiyat_id",
            "siparis_kalemi_id",
            name="uq_sevkiyat_kalemi_plan_siparis_kalem",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sevkiyat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sevkiyat_planlari.id"), nullable=False
    )
    siparis_kalemi_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("siparis_kalemleri.id"), nullable=False
    )
    urun_id: Mapped[int] = mapped_column(Integer, ForeignKey("urunler.id"), nullable=False)
    miktar: Mapped[int] = mapped_column(Integer, nullable=False)

    # İlişkiler
    sevkiyat: Mapped["SevkiyatPlani"] = relationship("SevkiyatPlani", back_populates="kalemler")
    siparis_kalemi: Mapped["SiparisKalemi"] = relationship("SiparisKalemi")
    urun: Mapped["Urun"] = relationship("Urun")


# ========================
# İRSALİYE
# ========================

class Irsaliye(Base):
    __tablename__ = "irsaliyeler"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    siparis_id: Mapped[int] = mapped_column(Integer, ForeignKey("siparisler.id"), nullable=False)
    sevkiyat_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sevkiyat_planlari.id"), nullable=True)
    irsaliye_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    irsaliye_tarihi: Mapped[date] = mapped_column(Date, nullable=False)
    belge_turu: Mapped[str] = mapped_column(String(50), default="SevkIrsaliyesi")
    tir_plaka: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sofor_adi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Taslak")
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
)

    # İlişkiler
    siparis: Mapped["Siparis"] = relationship("Siparis", back_populates="irsaliyeler")


# ========================
# MAL KABUL İRSALİYESİ
# ========================

class MalKabulIrsaliye(Base):
    __tablename__ = "mal_kabul_irsaliyeleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    irsaliye_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    tedarikci_id: Mapped[int] = mapped_column(Integer, ForeignKey("tedarikciler.id"), nullable=False)
    depo_id: Mapped[int] = mapped_column(Integer, ForeignKey("depolar.id"), nullable=False)
    tir_plaka: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sofor_adi: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Taslak")
    tarih: Mapped[date] = mapped_column(Date, nullable=False)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
    )
    kapanma_ozeti: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # İlişkiler
    tedarikci: Mapped["Tedarikci"] = relationship("Tedarikci")
    depo: Mapped["Depo"] = relationship("Depo")
    kalemler: Mapped[list["MalKabulKalemi"]] = relationship(
        "MalKabulKalemi", back_populates="irsaliye", cascade="all, delete-orphan"
    )


# ========================
# MAL KABUL KALEMİ
# ========================

class MalKabulKalemi(Base):
    __tablename__ = "mal_kabul_kalemleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    mal_kabul_irsaliyesi_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("mal_kabul_irsaliyeleri.id"), nullable=False
    )
    palet_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    urun_id: Mapped[int] = mapped_column(Integer, ForeignKey("urunler.id"), nullable=False)
    lot_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    miktar: Mapped[int] = mapped_column(Integer, nullable=False)
    raf_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("raflar.id"), nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Bekliyor")
    uretim_tarihi: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    son_kullanma_tarihi: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    istisna_tip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    istisna_aciklama: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gerceklesen_miktar: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # İlişkiler
    irsaliye: Mapped["MalKabulIrsaliye"] = relationship("MalKabulIrsaliye", back_populates="kalemler")
    urun: Mapped["Urun"] = relationship("Urun")
    raf: Mapped[Optional["Raf"]] = relationship("Raf")


# ========================
# BELGE TASLAGI
# ========================

class BelgeTaslagi(Base):
    __tablename__ = "belge_taslaklari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kaynak_dosya_yolu: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    belge_tipi: Mapped[str] = mapped_column(String(50), default="IRSALIYE", nullable=False, index=True)
    ham_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    durum: Mapped[str] = mapped_column(String(30), default="KABUL_BEKLIYOR", nullable=False, index=True)
    confidence_skoru: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    olusturan_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True, index=True
    )
    depo_id: Mapped[int] = mapped_column(Integer, ForeignKey("depolar.id"), nullable=False, index=True)
    mal_kabul_irsaliye_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("mal_kabul_irsaliyeleri.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
        server_onupdate=func.now(),
    )

    olusturan_kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici")
    depo: Mapped["Depo"] = relationship("Depo")
    mal_kabul_irsaliye: Mapped[Optional["MalKabulIrsaliye"]] = relationship("MalKabulIrsaliye")


# ========================
# RAPOR SABLONU
# ========================

class RaporSablonu(Base):
    __tablename__ = "rapor_sablonlari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ad: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    tur: Mapped[str] = mapped_column(String(50), nullable=False)
    aciklama: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    olusturan_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    is_aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
    )

    # İlişkiler
    olusturan_kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici")
    raporlar: Mapped[list["RaporLogu"]] = relationship("RaporLogu", back_populates="sablon")


# ========================
# RAPOR LOGU
# ========================

class RaporLogu(Base):
    __tablename__ = "rapor_loglari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sablon_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("rapor_sablonlari.id"), nullable=True)
    kullanici_id: Mapped[int] = mapped_column(Integer, ForeignKey("kullanicilar.id"), nullable=False)
    parametreler: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Basarili")
    hata_mesaji: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    tamamlanma_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # İlişkiler
    sablon: Mapped[Optional["RaporSablonu"]] = relationship("RaporSablonu", back_populates="raporlar")
    kullanici: Mapped["Kullanici"] = relationship("Kullanici")


# ========================
# RAPOR ZAMANLAMA
# ========================

class RaporSchedule(Base):
    __tablename__ = "rapor_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sablon_id: Mapped[int] = mapped_column(Integer, ForeignKey("rapor_sablonlari.id"), nullable=False)
    sablon_adi: Mapped[str] = mapped_column(String(200), nullable=False)
    periyod: Mapped[str] = mapped_column(String(20), nullable=False)
    saat: Mapped[str] = mapped_column(String(5), nullable=False)
    alici_emailler: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    format: Mapped[str] = mapped_column(String(20), default="pdf")
    is_aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    son_calistirilma: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())
    guncelleme_tarihi: Mapped[datetime] = mapped_column(
    DateTime, 
    default=datetime.utcnow, 
    onupdate=datetime.utcnow,
    server_default=func.now(),       # DB'de ilk oluşurken atanacak default
    server_onupdate=func.now()       # DB'de raw sql ile güncellenirse atanacak değer
    )

    # İlişkiler
    sablon: Mapped["RaporSablonu"] = relationship("RaporSablonu")


# ========================
# STOK SAYIM  (Inventar)
# ========================

class StokSayim(Base):
    """Periyodik stok sayımı oturumu (header)"""
    __tablename__ = "stok_sayimlar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sayim_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    aciklama: Mapped[str] = mapped_column(Text, default="")

    baslangic_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    bitis_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    referans_stok_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    kontrol_eden_user_id: Mapped[int] = mapped_column(Integer, ForeignKey("kullanicilar.id"))
    onaylayan_user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )

    durum: Mapped[str] = mapped_column(String(20), default="oluşturuldu")

    aktif: Mapped[bool] = mapped_column(Boolean, default=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now())

    # İlişkiler
    sayim_kalemleri: Mapped[list["StokSayimKalemi"]] = relationship(
        "StokSayimKalemi", back_populates="sayim", cascade="all, delete-orphan"
    )
    kontrol_eden: Mapped["Kullanici"] = relationship(
        "Kullanici", foreign_keys="StokSayim.kontrol_eden_user_id"
    )
    onaylayan: Mapped[Optional["Kullanici"]] = relationship(
        "Kullanici", foreign_keys="StokSayim.onaylayan_user_id"
    )


class StokSayimKalemi(Base):
    """Stok sayımı satır öğeleri (ürün başına sayılan miktar)"""
    __tablename__ = "stok_sayim_kalemleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    sayim_id: Mapped[int] = mapped_column(Integer, ForeignKey("stok_sayimlar.id"), nullable=False, index=True)
    urun_id: Mapped[int] = mapped_column(Integer, ForeignKey("urunler.id"), nullable=False, index=True)

    sayilan_miktar: Mapped[int] = mapped_column(Integer, default=0)
    notlar: Mapped[str] = mapped_column(Text, default="")

    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("kullanicilar.id"))
    sayim_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # İlişkiler
    sayim: Mapped["StokSayim"] = relationship("StokSayim", back_populates="sayim_kalemleri")
    urun: Mapped["Urun"] = relationship("Urun")
    user: Mapped[Optional["Kullanici"]] = relationship("Kullanici", foreign_keys="StokSayimKalemi.user_id")


# ========================
# YERLEŞTİRME GÖREVİ
# ========================

class YerlestirmeGorevi(Base):
    __tablename__ = "yerlestirme_gorevleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    palet_id: Mapped[int] = mapped_column(Integer, ForeignKey("paletler.id"), nullable=False)
    mal_kabul_irsaliye_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("mal_kabul_irsaliyeleri.id"), nullable=True
    )
    depo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("depolar.id"), nullable=True, index=True)
    tip: Mapped[str] = mapped_column(String(20), default="Yerlestirme", nullable=False)
    kaynak_raf_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("raflar.id"), nullable=True)
    onerilen_raf_id: Mapped[int] = mapped_column(Integer, ForeignKey("raflar.id"), nullable=False)
    gerceklesen_raf_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("raflar.id"), nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Bekliyor", nullable=False, index=True)
    oncelik: Mapped[int] = mapped_column(Integer, default=5, index=True)
    atanan_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    override_kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    override_neden: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now(), index=True)
    atanma_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    baslama_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tamamlanma_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    iptal_nedeni: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # İlişkiler
    palet: Mapped["Palet"] = relationship("Palet")
    kaynak_raf: Mapped[Optional["Raf"]] = relationship("Raf", foreign_keys=[kaynak_raf_id])
    onerilen_raf: Mapped["Raf"] = relationship("Raf", foreign_keys=[onerilen_raf_id])
    gerceklesen_raf: Mapped[Optional["Raf"]] = relationship("Raf", foreign_keys=[gerceklesen_raf_id])
    atanan_kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici", foreign_keys=[atanan_kullanici_id])
    override_kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici", foreign_keys=[override_kullanici_id])


# ========================
# TOPLAMA GÖREVİ
# ========================

class ToplamaGorevi(Base):
    """Palet bazlı toplama (pick task) görevi."""
    __tablename__ = "toplama_gorevleri"
    __table_args__ = (
        Index(
            "ix_toplama_gorevleri_queue_lookup",
            "durum",
            "depo_id",
            "sira_no",
            "olusturma_tarihi",
            "id",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sevkiyat_id: Mapped[int] = mapped_column(Integer, ForeignKey("sevkiyat_planlari.id"), nullable=False, index=True)
    palet_id: Mapped[int] = mapped_column(Integer, ForeignKey("paletler.id"), nullable=False, index=True)
    lot_id: Mapped[int] = mapped_column(Integer, ForeignKey("lotlar.id"), nullable=False)
    urun_id: Mapped[int] = mapped_column(Integer, ForeignKey("urunler.id"), nullable=False)
    depo_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("depolar.id"), nullable=True, index=True)
    atanan_kullanici_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Beklemede", nullable=False, index=True)
    fefo_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    override_neden: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    override_kullanici_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    sira_no: Mapped[int] = mapped_column(Integer, default=0, nullable=False, index=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, server_default=func.now(), index=True)
    atanma_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    baslama_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    tamamlanma_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    iptal_nedeni: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # İlişkiler
    palet: Mapped["Palet"] = relationship("Palet", foreign_keys=[palet_id])
    urun: Mapped["Urun"] = relationship("Urun", foreign_keys=[urun_id])
    lot: Mapped["Lot"] = relationship("Lot", foreign_keys=[lot_id])
    atanan_kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici", foreign_keys=[atanan_kullanici_id])
    override_kullanici: Mapped[Optional["Kullanici"]] = relationship("Kullanici", foreign_keys=[override_kullanici_id])


# ========================
# PALET REZERVASYONU
# ========================

class PaletRezervasyonu(Base):
    """Sipariş → Palet rezervasyonu (lifecycle: Aktif → Kesinlesti | IptalEdildi)."""
    __tablename__ = "palet_rezervasyonlari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    palet_id: Mapped[int] = mapped_column(Integer, ForeignKey("paletler.id"), nullable=False, index=True)
    siparis_id: Mapped[int] = mapped_column(Integer, ForeignKey("siparisler.id"), nullable=False, index=True)
    sevkiyat_kalemi_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sevkiyat_kalemleri.id"), nullable=True)
    durum: Mapped[str] = mapped_column(String(20), default="Aktif", nullable=False, index=True)
    rezerve_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    kesinlesme_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    iptal_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    iptal_nedeni: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # İlişkiler
    palet: Mapped["Palet"] = relationship("Palet", foreign_keys=[palet_id])
    siparis: Mapped["Siparis"] = relationship("Siparis", foreign_keys=[siparis_id])


# ========================
# IDEMPOTENCY KAYDI
# ========================

class IdempotencyKaydi(Base):
    """Kritik POST endpoint'leri için retry-safe idempotency tablosu.
    Composite PK: (idempotency_key, endpoint) — aynı key farklı endpoint'lerde bağımsız.
    TTL: 24 saat (son_kullanim_tarihi aşıldıktan sonra startup cleanup ile silinir).
    """
    __tablename__ = "idempotency_kayitlari"
    __table_args__ = (
        PrimaryKeyConstraint("idempotency_key", "endpoint"),
    )

    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False)
    response_body: Mapped[dict] = mapped_column(JSON, nullable=False)
    olusturma_tarihi: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    son_kullanim_tarihi: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


# ========================
# ETİKET ŞABLONU
# ========================

class EtiketSablonu(Base):
    __tablename__ = "etiket_sablonlari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    ad: Mapped[str] = mapped_column(String(100), nullable=False)
    boyut: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    zpl_template: Mapped[str] = mapped_column(Text, nullable=False)
    html_template: Mapped[str] = mapped_column(Text, nullable=False)
    default_mi: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    aktif: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    olusturan_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False
    )


# ========================
# PALET ETİKET
# ========================

class PaletEtiket(Base):
    __tablename__ = "palet_etiketleri"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    palet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("paletler.id"), nullable=False, index=True
    )
    sablon_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("etiket_sablonlari.id"), nullable=False, index=True
    )
    render_edilmis_zpl: Mapped[str] = mapped_column(Text, nullable=False)
    render_edilmis_html: Mapped[str] = mapped_column(Text, nullable=False)
    barkod_deger: Mapped[str] = mapped_column(String(100), nullable=False)
    qr_deger: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    basim_sayisi: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    son_basim_tarihi: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    kullanici_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=True
    )
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False
    )

    palet: Mapped["Palet"] = relationship("Palet", foreign_keys=[palet_id])
    sablon: Mapped["EtiketSablonu"] = relationship("EtiketSablonu", foreign_keys=[sablon_id])


# ========================
# TALEP TAHMİNİ CACHE
# ========================

class TalepTahminCache(Base):
    """Nightly job tarafindan hesaplanan tahmin payload'ini saklar.

    Frontend on-demand istegi cache'den okur — model uretim runtime'inda
    egitilmez. Eger cache miss olursa router on-demand hesaplar ve sonra
    yazar (write-through).
    """
    __tablename__ = "talep_tahmin_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    urun_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("urunler.id"), nullable=False, index=True
    )
    tahmin_gun: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    stok_riski: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    tahmini_talep: Mapped[float] = mapped_column(default=0.0, nullable=False)
    onerilen_ikmal: Mapped[float] = mapped_column(default=0.0, nullable=False)
    veri_guven_skoru: Mapped[float] = mapped_column(default=0.0, nullable=False)
    model_versiyonu: Mapped[str] = mapped_column(String(80), nullable=False)
    hesaplanma_tarihi: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), nullable=False, index=True,
    )

    __table_args__ = (
        UniqueConstraint("urun_id", "tahmin_gun", name="uq_talep_tahmin_cache_urun_ufuk"),
    )


# ========================
# OPERATÖR PERFORMANS — LMS (Faz 1)
# ========================

class GorevPerformansEvent(Base):
    """Görev yaşam döngüsü olaylarının immutable log'u (transactional outbox).

    Yerleştirme veya toplama görevi BAŞLATILDI/TAMAMLANDI/IPTAL olduğunda
    use case kendi transaction'ı içinde buraya bir kayıt insert eder.
    APScheduler aggregator job `aggregate_edildi=False` kayıtları okuyup
    `operator_vardiya_metrikleri` tablosuna upsert eder.
    """

    __tablename__ = "gorev_performans_eventleri"
    __table_args__ = (
        Index(
            "ix_gorev_performans_event_outbox",
            "aggregate_edildi",
            "olusturma_tarihi",
        ),
        Index(
            "ix_gorev_performans_event_kullanici_tarih",
            "kullanici_id",
            "olusturma_tarihi",
        ),
        Index(
            "ix_gorev_performans_event_relay_outbox",
            "rabbitmq_yayinlandi",
            "olusturma_tarihi",
        ),
        UniqueConstraint(
            "event_uuid",
            name="uq_gorev_performans_eventleri_event_uuid",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_uuid: Mapped[str] = mapped_column(String(36), nullable=False)
    event_tipi: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    gorev_tipi: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    gorev_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    kullanici_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=False, index=True
    )
    depo_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("depolar.id"), nullable=True, index=True
    )
    sure_saniye: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    iptal_nedeni: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    aggregate_edildi: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False, index=True
    )
    rabbitmq_yayinlandi: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="0", nullable=False, index=True
    )
    rabbitmq_yayin_tarihi: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    rabbitmq_deneme_sayisi: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    rabbitmq_son_hata: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    olusturma_tarihi: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    kullanici: Mapped["Kullanici"] = relationship("Kullanici", foreign_keys=[kullanici_id])


class OperatorVardiyaMetrikleri(Base):
    """Bir operatörün bir takvim günü için aggregate edilmiş performans özeti.

    Aggregator job `gorev_performans_eventleri` üzerinden upsert eder. UPH
    okuma sırasında hesaplanır: (tamamlanan_yerlestirme + tamamlanan_toplama)
    / (toplam_aktif_saniye / 3600). Vardiya = takvim günü (00:00–23:59 UTC).
    """

    __tablename__ = "operator_vardiya_metrikleri"
    __table_args__ = (
        UniqueConstraint(
            "kullanici_id",
            "vardiya_tarihi",
            name="uq_operator_vardiya_metrikleri_kullanici_tarih",
        ),
        Index(
            "ix_operator_vardiya_metrikleri_depo_tarih",
            "depo_id",
            "vardiya_tarihi",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kullanici_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=False, index=True
    )
    depo_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("depolar.id"), nullable=True, index=True
    )
    vardiya_tarihi: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    tamamlanan_yerlestirme: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    tamamlanan_toplama: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    iptal_sayisi: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    toplam_aktif_saniye: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    ortalama_gorev_suresi_sn: Mapped[float] = mapped_column(
        Float, default=0.0, server_default="0", nullable=False
    )
    son_guncelleme: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )

    kullanici: Mapped["Kullanici"] = relationship("Kullanici", foreign_keys=[kullanici_id])


class AsistanAksiyonTaslagi(Base):
    __tablename__ = "asistan_aksiyon_taslaklari"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    kullanici_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("kullanicilar.id"), nullable=False, index=True
    )
    rol: Mapped[str] = mapped_column(String(32), nullable=False)
    tool_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    durum: Mapped[str] = mapped_column(
        String(30), default="BEKLEMEDE", nullable=False, index=True
    )
    ozet: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(
        String(128), nullable=False, unique=True
    )
    sonuc_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hata_mesaji: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, server_default=func.now(), index=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    kullanici: Mapped["Kullanici"] = relationship("Kullanici", foreign_keys=[kullanici_id])


from sqlalchemy.orm import column_property  # noqa: E402

# N+1 Problemini çözmek için column_property ile veritabanı seviyesinde toplama yapıyoruz.
Urun.stok_miktari = column_property(
    select(func.coalesce(func.sum(Palet.koli_adedi), 0))
    .select_from(Lot)
    .join(Palet, Lot.id == Palet.lot_id)
    .where(Lot.urun_id == Urun.id)
    .where(Lot.aktif)
    .where(Palet.aktif)
    .correlate(Urun)
    .scalar_subquery()
)
