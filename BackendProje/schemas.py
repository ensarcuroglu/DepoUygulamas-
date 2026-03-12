from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


# ========================
# MARKA ŞEMALARİ
# ========================

class MarkaBase(BaseModel):
    isim: str
    aciklama: Optional[str] = ""

class MarkaCreate(MarkaBase):
    pass

class MarkaUpdate(BaseModel):
    isim: Optional[str] = None
    aciklama: Optional[str] = None
    aktif: Optional[bool] = None

class MarkaResponse(MarkaBase):
    id: int
    aktif: bool
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# KATEGORİ ŞEMALARİ
# ========================

class KategoriBase(BaseModel):
    isim: str
    aciklama: Optional[str] = ""

class KategoriCreate(KategoriBase):
    pass

class KategoriUpdate(BaseModel):
    isim: Optional[str] = None
    aciklama: Optional[str] = None
    aktif: Optional[bool] = None

class KategoriResponse(KategoriBase):
    id: int
    aktif: bool
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# DEPO ŞEMALARİ
# ========================

class DepoBase(BaseModel):
    isim: str
    adres: Optional[str] = ""
    aciklama: Optional[str] = ""

class DepoCreate(DepoBase):
    pass

class DepoUpdate(BaseModel):
    isim: Optional[str] = None
    adres: Optional[str] = None
    aciklama: Optional[str] = None
    aktif: Optional[bool] = None

class DepoResponse(DepoBase):
    id: int
    aktif: bool
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# RAF ŞEMALARİ
# ========================

class RafBase(BaseModel):
    depo_id: Optional[int] = None
    kod: str
    bolge: Optional[str] = ""
    kapasite: Optional[int] = 100

class RafCreate(RafBase):
    pass

class RafUpdate(BaseModel):
    depo_id: Optional[int] = None
    kod: Optional[str] = None
    bolge: Optional[str] = None
    kapasite: Optional[int] = None
    aktif: Optional[bool] = None

class RafResponse(RafBase):
    id: int
    aktif: bool
    depo: Optional[DepoResponse] = None
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# TEDARİKÇİ ŞEMALARİ
# ========================

class TedarikciBase(BaseModel):
    firma_adi: str
    iletisim_kisi: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    adres: Optional[str] = None
    vergi_no: Optional[str] = None

class TedarikciCreate(TedarikciBase):
    pass

class TedarikciUpdate(BaseModel):
    firma_adi: Optional[str] = None
    iletisim_kisi: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    adres: Optional[str] = None
    vergi_no: Optional[str] = None
    aktif: Optional[bool] = None

class TedarikciResponse(TedarikciBase):
    id: int
    aktif: bool
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# ÜRÜN ŞEMALARİ
# ========================

class UrunBase(BaseModel):
    isim: str
    marka_id: Optional[int] = None
    kategori_id: Optional[int] = None
    tedarikci_id: Optional[int] = None
    ean: Optional[str] = None
    barkod: Optional[str] = None
    ic_adet: Optional[int] = 1
    gramaj: Optional[float] = None
    birim: Optional[str] = "Adet"
    fiyat: Optional[float] = 0.0
    min_stok: Optional[int] = 10
    aciklama: Optional[str] = ""

class UrunCreate(UrunBase):
    pass

class UrunUpdate(BaseModel):
    isim: Optional[str] = None
    marka_id: Optional[int] = None
    kategori_id: Optional[int] = None
    tedarikci_id: Optional[int] = None
    ean: Optional[str] = None
    barkod: Optional[str] = None
    ic_adet: Optional[int] = None
    gramaj: Optional[float] = None
    birim: Optional[str] = None
    fiyat: Optional[float] = None
    min_stok: Optional[int] = None
    aciklama: Optional[str] = None
    aktif: Optional[bool] = None

class UrunResponse(UrunBase):
    id: int
    stok_miktari: int
    durum: str
    aktif: bool
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    marka: Optional[MarkaResponse] = None
    kategori: Optional[KategoriResponse] = None
    tedarikci: Optional[TedarikciResponse] = None

    class Config:
        from_attributes = True

class UrunListResponse(BaseModel):
    id: int
    isim: str
    barkod: Optional[str] = None
    ean: Optional[str] = None
    ic_adet: Optional[int] = None
    gramaj: Optional[float] = None
    marka: Optional[MarkaResponse] = None
    kategori: Optional[KategoriResponse] = None
    stok_miktari: int
    birim: str
    fiyat: float
    durum: str
    aktif: bool

    class Config:
        from_attributes = True


# ========================
# LOT ŞEMALARİ
# ========================

class LotBase(BaseModel):
    urun_id: int
    lot_no: Optional[str] = None
    parti_no: Optional[str] = None
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    aciklama: Optional[str] = ""

class LotCreate(LotBase):
    pass

class LotUpdate(BaseModel):
    lot_no: Optional[str] = None
    parti_no: Optional[str] = None
    uretim_tarihi: Optional[date] = None
    son_kullanma_tarihi: Optional[date] = None
    aciklama: Optional[str] = None
    aktif: Optional[bool] = None

class LotResponse(LotBase):
    id: int
    aktif: bool
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True

class LotDetailResponse(LotResponse):
    urun: Optional[UrunListResponse] = None

    class Config:
        from_attributes = True


# ========================
# PALET ŞEMALARİ
# ========================

class PaletBase(BaseModel):
    lot_id: int
    raf_id: Optional[int] = None
    palet_no: str
    koli_adedi: int
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None

class PaletCreate(PaletBase):
    pass

class PaletUpdate(BaseModel):
    raf_id: Optional[int] = None
    koli_adedi: Optional[int] = None
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None
    aktif: Optional[bool] = None

class PaletResponse(PaletBase):
    id: int
    tarih: datetime
    aktif: bool
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True

class PaletDetailResponse(PaletResponse):
    lot: Optional[LotResponse] = None
    raf: Optional[RafResponse] = None

    class Config:
        from_attributes = True


# ========================
# STOK HAREKETİ ŞEMALARİ
# ========================

class StokHareketiBase(BaseModel):
    urun_id: int
    lot_id: Optional[int] = None
    palet_id: Optional[int] = None
    raf_id: Optional[int] = None
    hareket_tipi: str              # "giris" veya "cikis"
    miktar: int
    siparis_no: Optional[str] = None
    tir_plaka: Optional[str] = None
    depo_kapi: Optional[str] = None
    barkodlar: Optional[List[str]] = None
    aciklama: Optional[str] = ""

class StokHareketiCreate(StokHareketiBase):
    pass

class StokHareketiResponse(StokHareketiBase):
    id: int
    kullanici_id: Optional[int] = None
    kullanici: Optional[KullaniciResponse] = None
    raf: Optional[RafResponse] = None
    tarih: datetime

    class Config:
        from_attributes = True


# ========================
# SİSTEM LOGLARI ŞEMALARİ
# ========================

class SistemLogBase(BaseModel):
    kullanici_id: Optional[int] = None
    islem_tipi: str
    modul: str
    detay: Optional[str] = None
    eski_veri: Optional[dict] = None
    yeni_veri: Optional[dict] = None

class SistemLogCreate(SistemLogBase):
    pass

class SistemLogResponse(SistemLogBase):
    id: int
    tarih: datetime
    kullanici_ad_soyad: Optional[str] = None # Frontend'de göstermek için

    class Config:
        from_attributes = True


# ========================
# KULLANICI ŞEMALARİ
# ========================

class KullaniciBase(BaseModel):
    kullanici_adi: str
    ad_soyad: str
    rol: Optional[str] = "depocu"
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None

class KullaniciCreate(KullaniciBase):
    sifre: str

class KullaniciUpdate(BaseModel):
    kullanici_adi: Optional[str] = None
    ad_soyad: Optional[str] = None
    rol: Optional[str] = None
    sifre: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None

class KullaniciResponse(KullaniciBase):
    id: int
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# AUTH ŞEMALARİ
# ========================

class LoginRequest(BaseModel):
    kullanici_adi: str
    sifre: str

class TokenUserInfo(BaseModel):
    id: int
    kullanici_adi: str
    ad_soyad: str
    rol: str
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: TokenUserInfo


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


# ========================
# DASHBOARD ŞEMALARİ
# ========================

class DashboardStats(BaseModel):
    toplam_urun: int
    kritik_stok_sayisi: int
    bugunku_hareket: int
    toplam_deger: float


# ========================
# DESTEK MASASI ŞEMALARİ
# ========================

class DestekTalebiBase(BaseModel):
    konu: str
    kategori: str
    oncelik: Optional[str] = "Normal"
    aciklama: str

class DestekTalebiCreate(DestekTalebiBase):
    pass

class DestekTalebiUpdate(BaseModel):
    durum: Optional[str] = None
    admin_cevabi: Optional[str] = None
    oncelik: Optional[str] = None

class DestekTalebiResponse(DestekTalebiBase):
    id: int
    kullanici_id: int
    durum: str
    admin_cevabi: Optional[str] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    kullanici: Optional[KullaniciResponse] = None

    class Config:
        from_attributes = True


# ========================
# SİPARİŞ ŞEMALARİ
# ========================

class SiparisKalemiBase(BaseModel):
    urun_id: int
    miktar: int
    birim_fiyat: float
    kdv_orani: Optional[float] = 18.0
    toplam: Optional[float] = None

class SiparisKalemiCreate(SiparisKalemiBase):
    pass

class SiparisKalemiResponse(SiparisKalemiBase):
    id: int
    siparis_id: int
    urun: Optional[UrunListResponse] = None

    class Config:
        from_attributes = True

class SiparisBase(BaseModel):
    musteri_adi: str
    teslimat_adresi: str
    teslimat_tarihi: date
    durum: Optional[str] = "Bekleme"
    top_miktar: Optional[int] = 0
    top_tutar: Optional[float] = 0.0
    notlar: Optional[str] = ""

class SiparisCreate(SiparisBase):
    kalemler: List[SiparisKalemiCreate]

class SiparisUpdate(BaseModel):
    musteri_adi: Optional[str] = None
    teslimat_adresi: Optional[str] = None
    teslimat_tarihi: Optional[date] = None
    durum: Optional[str] = None
    top_miktar: Optional[int] = None
    top_tutar: Optional[float] = None
    notlar: Optional[str] = None
    aktif: Optional[bool] = None

class SiparisResponse(SiparisBase):
    id: int
    siparis_no: str
    olusturan_kullanici_id: Optional[int] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    aktif: bool

    class Config:
        from_attributes = True

class SiparisDetayResponse(SiparisResponse):
    kalemler: List[SiparisKalemiResponse] = []

    class Config:
        from_attributes = True


# ========================
# SEVKİYAT PLANI ŞEMALARİ
# ========================

class SevkiyatPlaniBase(BaseModel):
    siparis_id: int
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    sofor_telefon: Optional[str] = None
    depo_kapi: Optional[str] = None
    yukleme_tarihi: date
    cikis_saati: Optional[str] = None
    varis_saati: Optional[str] = None
    durum: Optional[str] = "Planlandi"
    notlar: Optional[str] = ""

class SevkiyatPlaniCreate(SevkiyatPlaniBase):
    pass

class SevkiyatPlaniUpdate(BaseModel):
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    sofor_telefon: Optional[str] = None
    depo_kapi: Optional[str] = None
    yukleme_tarihi: Optional[date] = None
    cikis_saati: Optional[str] = None
    varis_saati: Optional[str] = None
    durum: Optional[str] = None
    notlar: Optional[str] = None

class SevkiyatPlaniResponse(SevkiyatPlaniBase):
    id: int
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    siparis: Optional[SiparisResponse] = None

    class Config:
        from_attributes = True


# ========================
# İRSALİYE ŞEMALARİ
# ========================

class IrsaliyeBase(BaseModel):
    siparis_id: int
    sevkiyat_id: Optional[int] = None
    irsaliye_tarihi: date
    belge_turu: Optional[str] = "SevkIrsaliyesi"
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: Optional[str] = "Taslak"

class IrsaliyeCreate(IrsaliyeBase):
    pass

class IrsaliyeUpdate(BaseModel):
    belge_turu: Optional[str] = None
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: Optional[str] = None

class IrsaliyeResponse(IrsaliyeBase):
    id: int
    irsaliye_no: str
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    siparis: Optional[SiparisResponse] = None

    class Config:
        from_attributes = True


# ========================
# RAPOR ŞABLONU ŞEMALARİ
# ========================

class RaporSablonuBase(BaseModel):
    ad: str
    tur: str
    aciklama: Optional[str] = ""
    config: Optional[dict] = None

class RaporSablonuCreate(RaporSablonuBase):
    pass

class RaporSablonuUpdate(BaseModel):
    ad: Optional[str] = None
    tur: Optional[str] = None
    aciklama: Optional[str] = None
    config: Optional[dict] = None
    is_aktif: Optional[bool] = None

class RaporSablonuResponse(RaporSablonuBase):
    id: int
    is_aktif: bool
    olusturan_kullanici_id: Optional[int] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# RAPOR LOGU ŞEMALARİ
# ========================

class RaporLoguBase(BaseModel):
    sablon_id: Optional[int] = None
    parametreler: Optional[dict] = None
    durum: Optional[str] = "Basarili"
    hata_mesaji: Optional[str] = None

class RaporLoguCreate(RaporLoguBase):
    pass

class RaporLoguResponse(RaporLoguBase):
    id: int
    kullanici_id: int
    olusturma_tarihi: datetime
    tamamlanma_tarihi: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================
# RAPOR ZAMANLAMA ŞEMALARİ
# ========================

class RaporScheduleBase(BaseModel):
    sablon_id: int
    sablon_adi: str
    periyod: str  # "gunluk", "haftalik", "aylik"
    saat: str  # HH:MM
    alici_emailler: Optional[List[str]] = None
    format: Optional[str] = "pdf"

class RaporScheduleCreate(RaporScheduleBase):
    pass

class RaporScheduleUpdate(BaseModel):
    sablon_adi: Optional[str] = None
    periyod: Optional[str] = None
    saat: Optional[str] = None
    alici_emailler: Optional[List[str]] = None
    format: Optional[str] = None
    is_aktif: Optional[bool] = None

class RaporScheduleResponse(RaporScheduleBase):
    id: int
    is_aktif: bool
    son_calistirilma: Optional[datetime] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# STOK SAYIM ŞEMALARİ
# ========================

class StokSayimKalemiBase(BaseModel):
    urun_id: int
    sayilan_miktar: int
    notlar: Optional[str] = ""

class StokSayimKalemiCreate(StokSayimKalemiBase):
    pass

class StokSayimKalemiRead(StokSayimKalemiBase):
    id: int
    sayim_id: int
    user_id: Optional[int] = None
    sayim_tarihi: datetime
    urun_adi: Optional[str] = None

    class Config:
        from_attributes = True

class StokSayimCreate(BaseModel):
    aciklama: Optional[str] = ""

class StokSayimRead(BaseModel):
    id: int
    sayim_no: str
    aciklama: str
    baslangic_tarihi: datetime
    bitis_tarihi: Optional[datetime] = None
    durum: str
    sayim_kalemleri: List[StokSayimKalemiRead] = []
    kontrol_eden_user_id: int
    onaylayan_user_id: Optional[int] = None
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True
