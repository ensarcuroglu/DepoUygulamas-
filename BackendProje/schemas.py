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
    token_type: str
    user: TokenUserInfo


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
