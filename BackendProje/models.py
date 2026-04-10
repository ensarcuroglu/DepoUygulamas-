from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

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
    ikon = Column(String(50), default="FolderOpen")
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
    zonlar = relationship("Zon", back_populates="depo")
    raflar = relationship("Raf", back_populates="depo")


# ========================
# ZON
# ========================

class Zon(Base):
    __tablename__ = "zonlar"

    id = Column(Integer, primary_key=True, index=True)
    depo_id = Column(Integer, ForeignKey("depolar.id"), nullable=False)
    isim = Column(String(100), nullable=False)
    tip = Column(String(30), nullable=False)                     # Or: MalKabul, Genel, Soguk...
    kod = Column(String(10), unique=True, nullable=False)
    aciklama = Column(Text, default="")
    sira = Column(Integer, default=0)
    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # Iliski
    depo = relationship("Depo", back_populates="zonlar")
    raflar = relationship("Raf", back_populates="zon")


# ========================
# RAF
# ========================

class Raf(Base):
    __tablename__ = "raflar"

    id = Column(Integer, primary_key=True, index=True)
    depo_id = Column(Integer, ForeignKey("depolar.id"), nullable=True)
    zon_id = Column(Integer, ForeignKey("zonlar.id"), nullable=True)   # Faz 0.2
    kod = Column(String(50), unique=True, nullable=False)              # Örn: "GNL-A-12-01-01"
    bolge = Column(String(50), default="")                             # DEPRECATED: zon_id kullanılır
    kapasite = Column(Integer, default=100)
    max_agirlik_kg = Column(Float, nullable=True)                      # Faz 0.2
    koridor = Column(String(10), default="")                           # Faz 0.2
    kat = Column(Integer, default=0)                                   # Faz 0.2
    goz = Column(Integer, default=0)                                   # Faz 0.2
    aktif = Column(Boolean, default=True)
    is_staging = Column(Boolean, default=False, nullable=False)  # MIGRATION_STAGING explicit bayrağı
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    depo = relationship("Depo", back_populates="raflar")
    zon = relationship("Zon", back_populates="raflar")
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
    depolama_tipi = Column(String(20), default="Kuru")           # DepolamaTipi: Kuru, Soguk, Tehlikeli
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
    raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=False)  # Adım 10 sonrası NOT NULL
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
    irsaliye_no = Column(String(100), nullable=True)              # Ürün girişi için Mal Kabul İrsaliye Numarası
    tir_plaka = Column(String(50), nullable=True)                 # Ürün çıkışı için Tır Plakası
    depo_kapi = Column(String(50), nullable=True)                 # Ürün çıkışı için Depo Kapısı
    barkodlar = Column(JSON, nullable=True)                       # Çoklu barkodları json array formatında saklamak için
    sofor_adi = Column(String(100), nullable=True)                # Çıkış için sürücü adı
    tasiyici_firma = Column(String(100), nullable=True)           # Çıkış için taşıyıcı/nakliye firması
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
    depo_id = Column(Integer, ForeignKey("depolar.id"), nullable=True)  # Atanmış depo (NULL = tüm depolar)
    depo_erisimi_yok = Column(Boolean, default=False, nullable=False)   # True = hiçbir depoda yetki yok
    refresh_token_hash = Column(String(255), nullable=True)        # Hashli refresh token
    refresh_token_son_kullanim = Column(DateTime, nullable=True)   # Refresh token geçerlilik süresi
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişki
    stok_hareketleri = relationship("StokHareketi", back_populates="kullanici")
    destek_talepleri = relationship("DestekTalebi", back_populates="kullanici")
    depo = relationship("Depo", foreign_keys=[depo_id])


# ========================
# DESTEK MASASI
# ========================

class DestekTalebi(Base):
    __tablename__ = "destek_talepleri"

    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=False)
    konu = Column(String(200), nullable=False)
    kategori = Column(String(50), nullable=False)                 # "Hata Bildirimi", "Donanım Talebi", "Diğer" vs.
    oncelik = Column(String(20), default="Normal")                # "Düşük", "Normal", "Yüksek"
    durum = Column(String(20), default="Açık")                    # "Açık", "İşlemde", "Çözüldü"
    aciklama = Column(Text, nullable=False)                       # Kullanıcının talebi
    admin_cevabi = Column(Text, nullable=True)                    # Yönetici/Destek ekibinin cevabı
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişki
    kullanici = relationship("Kullanici", back_populates="destek_talepleri")

# ========================
# SİPARİŞ
# ========================

class Siparis(Base):
    __tablename__ = "siparisler"

    id = Column(Integer, primary_key=True, index=True)
    siparis_no = Column(String(50), unique=True, nullable=False, index=True)  # Örn: SIP-2026-0001
    musteri_adi = Column(String(200), nullable=False)
    teslimat_adresi = Column(Text, nullable=False)
    teslimat_tarihi = Column(Date, nullable=False)
    durum = Column(String(20), default="Bekleme")  # Bekleme, Hazirlaniyor, YolaCikti, TeslimEdildi, Iptal
    top_miktar = Column(Integer, default=0)
    top_tutar = Column(Float, default=0.0)
    notlar = Column(Text, default="")
    olusturan_kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    aktif = Column(Boolean, default=True)

    # İlişkiler
    kalemler = relationship("SiparisKalemi", back_populates="siparis", cascade="all, delete-orphan")
    sevkiyat_plani = relationship("SevkiyatPlani", back_populates="siparis", uselist=False)
    irsaliyeler = relationship("Irsaliye", back_populates="siparis")
    olusturan_kullanici = relationship("Kullanici")


# ========================
# SİPARİŞ KALEMİ
# ========================

class SiparisKalemi(Base):
    __tablename__ = "siparis_kalemleri"

    id = Column(Integer, primary_key=True, index=True)
    siparis_id = Column(Integer, ForeignKey("siparisler.id"), nullable=False)
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False)
    miktar = Column(Integer, nullable=False)
    birim_fiyat = Column(Float, nullable=False)
    kdv_orani = Column(Float, default=18.0)
    toplam = Column(Float, nullable=False)

    # İlişkiler
    siparis = relationship("Siparis", back_populates="kalemler")
    urun = relationship("Urun")


# ========================
# SEVKİYAT PLANI
# ========================

class SevkiyatPlani(Base):
    __tablename__ = "sevkiyat_planlari"

    id = Column(Integer, primary_key=True, index=True)
    siparis_id = Column(Integer, ForeignKey("siparisler.id"), unique=True, nullable=False)
    tir_plaka = Column(String(20), nullable=True)
    sofor_adi = Column(String(100), nullable=True)
    sofor_telefon = Column(String(20), nullable=True)
    depo_kapi = Column(String(50), nullable=True)
    yukleme_tarihi = Column(Date, nullable=False)
    cikis_saati = Column(String(5), nullable=True)  # HH:MM format
    varis_saati = Column(String(5), nullable=True)  # HH:MM format
    durum = Column(String(20), default="Planlandi")  # Planlandi, Yukleniyor, Yolda, TeslimEdildi
    notlar = Column(Text, default="")
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    siparis = relationship("Siparis", back_populates="sevkiyat_plani")


# ========================
# İRSALİYE
# ========================

class Irsaliye(Base):
    __tablename__ = "irsaliyeler"

    id = Column(Integer, primary_key=True, index=True)
    siparis_id = Column(Integer, ForeignKey("siparisler.id"), nullable=False)
    sevkiyat_id = Column(Integer, ForeignKey("sevkiyat_planlari.id"), nullable=True)
    irsaliye_no = Column(String(50), unique=True, nullable=False, index=True)  # Örn: IRS-2026-0001
    irsaliye_tarihi = Column(Date, nullable=False)
    belge_turu = Column(String(50), default="SevkIrsaliyesi")  # SevkIrsaliyesi, IadeIrsaliyesi
    tir_plaka = Column(String(20), nullable=True)
    sofor_adi = Column(String(100), nullable=True)
    durum = Column(String(20), default="Taslak")  # Taslak, Kesildi, Gonderildi
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    siparis = relationship("Siparis", back_populates="irsaliyeler")


# ========================
# MAL KABUL İRSALİYESİ
# ========================

class MalKabulIrsaliye(Base):
    __tablename__ = "mal_kabul_irsaliyeleri"

    id = Column(Integer, primary_key=True, index=True)
    irsaliye_no = Column(String(50), unique=True, nullable=False, index=True)  # MKI-2026-00001
    tedarikci_id = Column(Integer, ForeignKey("tedarikciler.id"), nullable=False)
    depo_id = Column(Integer, ForeignKey("depolar.id"), nullable=False)
    tir_plaka = Column(String(20), nullable=True)
    sofor_adi = Column(String(100), nullable=True)
    durum = Column(String(20), default="Taslak")  # Taslak, Onaylandi, Kapandi
    tarih = Column(Date, nullable=False)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    kapanma_ozeti = Column(JSON, nullable=True)  # Otomatik kapanışta snapshot

    # İlişkiler
    tedarikci = relationship("Tedarikci")
    depo = relationship("Depo")
    kalemler = relationship("MalKabulKalemi", back_populates="irsaliye", cascade="all, delete-orphan")


# ========================
# MAL KABUL KALEMİ
# ========================

class MalKabulKalemi(Base):
    __tablename__ = "mal_kabul_kalemleri"

    id = Column(Integer, primary_key=True, index=True)
    mal_kabul_irsaliyesi_id = Column(Integer, ForeignKey("mal_kabul_irsaliyeleri.id"), nullable=False)
    palet_no = Column(String(30), unique=True, nullable=False, index=True)  # PLT-2026-00001
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False)
    lot_no = Column(String(50), nullable=True)
    miktar = Column(Integer, nullable=False)
    raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)
    durum = Column(String(20), default="Bekliyor")  # Bekliyor, GirisYapildi
    uretim_tarihi = Column(Date, nullable=True)
    son_kullanma_tarihi = Column(Date, nullable=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    istisna_tip = Column(String(50), nullable=True)
    istisna_aciklama = Column(Text, nullable=True)
    gerceklesen_miktar = Column(Integer, nullable=True)

    # İlişkiler
    irsaliye = relationship("MalKabulIrsaliye", back_populates="kalemler")
    urun = relationship("Urun")
    raf = relationship("Raf")


# ========================
# RAPOR ŞABLONU
# ========================

class RaporSablonu(Base):
    __tablename__ = "rapor_sablonlari"

    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(200), nullable=False, index=True)
    tur = Column(String(50), nullable=False)  # "stok", "siparis", "finansal", "performans"
    aciklama = Column(Text, default="")
    config = Column(JSON, nullable=True)  # { "columns": [...], "filters": {...}, "groupBy": "..." }
    olusturan_kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    is_aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    olusturan_kullanici = relationship("Kullanici")
    raporlar = relationship("RaporLogu", back_populates="sablon")


# ========================
# RAPOR LOGU
# ========================

class RaporLogu(Base):
    __tablename__ = "rapor_loglari"

    id = Column(Integer, primary_key=True, index=True)
    sablon_id = Column(Integer, ForeignKey("rapor_sablonlari.id"), nullable=True)
    kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=False)
    parametreler = Column(JSON, nullable=True)  # Rapor oluştururken kullanılan parametreler
    durum = Column(String(20), default="Basarili")  # "Basarili", "Hatali"
    hata_mesaji = Column(Text, nullable=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    tamamlanma_tarihi = Column(DateTime, nullable=True)

    # İlişkiler
    sablon = relationship("RaporSablonu", back_populates="raporlar")
    kullanici = relationship("Kullanici")


# ========================
# RAPOR ZAMANLAMA
# ========================

class RaporSchedule(Base):
    __tablename__ = "rapor_schedules"

    id = Column(Integer, primary_key=True, index=True)
    sablon_id = Column(Integer, ForeignKey("rapor_sablonlari.id"), nullable=False)
    sablon_adi = Column(String(200), nullable=False)  # Deskriptif ad
    periyod = Column(String(20), nullable=False)  # "gunluk", "haftalik", "aylik"
    saat = Column(String(5), nullable=False)  # HH:MM format, örn: "09:00"
    alici_emailler = Column(JSON, nullable=True)  # ["email1@test.com", "email2@test.com"]
    format = Column(String(20), default="pdf")  # "pdf", "excel", "csv"
    is_aktif = Column(Boolean, default=True)
    son_calistirilma = Column(DateTime, nullable=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)
    guncelleme_tarihi = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # İlişkiler
    sablon = relationship("RaporSablonu")


# ========================
# STOK SAYIM  (Inventar)
# ========================

class StokSayim(Base):
    """Periyodik stok sayımı oturumu (header)"""
    __tablename__ = "stok_sayimlar"

    id = Column(Integer, primary_key=True, index=True)
    sayim_no = Column(String(50), unique=True, nullable=False, index=True)
    aciklama = Column(Text, default="")

    # Sayım Dönemi
    baslangic_tarihi = Column(DateTime, default=datetime.utcnow)
    bitis_tarihi = Column(DateTime, nullable=True)

    # Snapshot alındığı andaki stok
    referans_stok_json = Column(JSON, nullable=True)  # {urun_id: koli_adedi, ...}

    # Sayımı yapan kullanıcı
    kontrol_eden_user_id = Column(Integer, ForeignKey("kullanicilar.id"))
    onaylayan_user_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)

    # Durum: "oluşturuldu", "devam_ediyor", "bitti", "onaylandı"
    durum = Column(String(20), default="oluşturuldu")

    aktif = Column(Boolean, default=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    sayim_kalemleri = relationship("StokSayimKalemi", back_populates="sayim", cascade="all, delete-orphan")
    kontrol_eden = relationship("Kullanici", foreign_keys="StokSayim.kontrol_eden_user_id")
    onaylayan = relationship("Kullanici", foreign_keys="StokSayim.onaylayan_user_id")


class StokSayimKalemi(Base):
    """Stok sayımı satır öğeleri (ürün başına sayılan miktar)"""
    __tablename__ = "stok_sayim_kalemleri"

    id = Column(Integer, primary_key=True, index=True)

    sayim_id = Column(Integer, ForeignKey("stok_sayimlar.id"), nullable=False, index=True)
    urun_id = Column(Integer, ForeignKey("urunler.id"), nullable=False, index=True)

    # Sayım sırasında kaydedilen miktar (koli)
    sayilan_miktar = Column(Integer, default=0)

    # Gözlem notları (hasarlı, yer değişmiş, vb)
    notlar = Column(Text, default="")

    # Sayımı yapan kişi
    user_id = Column(Integer, ForeignKey("kullanicilar.id"))

    sayim_tarihi = Column(DateTime, default=datetime.utcnow)

    # İlişkiler
    sayim = relationship("StokSayim", back_populates="sayim_kalemleri")
    urun = relationship("Urun")
    user = relationship("Kullanici", foreign_keys="StokSayimKalemi.user_id")


# ========================
# YERLEŞTİRME GÖREVİ
# ========================

class YerlestirmeGorevi(Base):
    __tablename__ = "yerlestirme_gorevleri"

    id = Column(Integer, primary_key=True, index=True)
    palet_id = Column(Integer, ForeignKey("paletler.id"), nullable=False)
    mal_kabul_irsaliye_id = Column(Integer, ForeignKey("mal_kabul_irsaliyeleri.id"), nullable=True)
    depo_id = Column(Integer, ForeignKey("depolar.id"), nullable=True, index=True)
    tip = Column(String(20), default="Yerlestirme", nullable=False)           # GorevTipi
    kaynak_raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)   # Transfer için
    onerilen_raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=False)
    gerceklesen_raf_id = Column(Integer, ForeignKey("raflar.id"), nullable=True)
    durum = Column(String(20), default="Bekliyor", nullable=False, index=True)
    oncelik = Column(Integer, default=5, index=True)
    atanan_kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    override_kullanici_id = Column(Integer, ForeignKey("kullanicilar.id"), nullable=True)
    override_neden = Column(Text, nullable=True)
    olusturma_tarihi = Column(DateTime, default=datetime.utcnow, index=True)
    atanma_tarihi = Column(DateTime, nullable=True, index=True)   # Timeout kontrolü için
    baslama_tarihi = Column(DateTime, nullable=True)
    tamamlanma_tarihi = Column(DateTime, nullable=True)
    iptal_nedeni = Column(Text, nullable=True)

    # İlişkiler
    palet = relationship("Palet")
    kaynak_raf = relationship("Raf", foreign_keys=[kaynak_raf_id])
    onerilen_raf = relationship("Raf", foreign_keys=[onerilen_raf_id])
    gerceklesen_raf = relationship("Raf", foreign_keys=[gerceklesen_raf_id])
    atanan_kullanici = relationship("Kullanici", foreign_keys=[atanan_kullanici_id])
    override_kullanici = relationship("Kullanici", foreign_keys=[override_kullanici_id])


from sqlalchemy import select, func # noqa: E402
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
