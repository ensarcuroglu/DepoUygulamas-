from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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

class KategoriResponse(KategoriBase):
    id: int

    class Config:
        from_attributes = True


# ========================
# RAF ŞEMALARİ
# ========================

class RafBase(BaseModel):
    kod: str
    bolge: Optional[str] = ""
    kapasite: Optional[int] = 100

class RafCreate(RafBase):
    pass

class RafUpdate(BaseModel):
    kod: Optional[str] = None
    bolge: Optional[str] = None
    kapasite: Optional[int] = None

class RafResponse(RafBase):
    id: int

    class Config:
        from_attributes = True


# ========================
# ÜRÜN ŞEMALARİ
# ========================

class UrunBase(BaseModel):
    isim: str
    barkod: Optional[str] = None
    aciklama: Optional[str] = ""
    kategori_id: Optional[int] = None
    raf_id: Optional[int] = None
    stok_miktari: Optional[int] = 0
    min_stok: Optional[int] = 10
    birim: Optional[str] = "Adet"
    fiyat: Optional[float] = 0.0

class UrunCreate(UrunBase):
    pass

class UrunUpdate(BaseModel):
    isim: Optional[str] = None
    barkod: Optional[str] = None
    aciklama: Optional[str] = None
    kategori_id: Optional[int] = None
    raf_id: Optional[int] = None
    stok_miktari: Optional[int] = None
    min_stok: Optional[int] = None
    birim: Optional[str] = None
    fiyat: Optional[float] = None

class UrunResponse(UrunBase):
    id: int
    durum: str
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    kategori: Optional[KategoriResponse] = None
    raf: Optional[RafResponse] = None

    class Config:
        from_attributes = True

class UrunListResponse(BaseModel):
    id: int
    isim: str
    barkod: Optional[str] = None
    kategori: Optional[KategoriResponse] = None
    raf: Optional[RafResponse] = None
    stok_miktari: int
    birim: str
    fiyat: float
    durum: str

    class Config:
        from_attributes = True


# ========================
# STOK HAREKETİ ŞEMALARİ
# ========================

class StokHareketiBase(BaseModel):
    urun_id: int
    hareket_tipi: str          # "giris" veya "cikis"
    miktar: int
    aciklama: Optional[str] = ""

class StokHareketiCreate(StokHareketiBase):
    pass

class StokHareketiResponse(StokHareketiBase):
    id: int
    kullanici_id: Optional[int] = None
    tarih: datetime

    class Config:
        from_attributes = True


# ========================
# KULLANICI ŞEMALARİ
# ========================

class KullaniciBase(BaseModel):
    kullanici_adi: str
    ad_soyad: str
    rol: Optional[str] = "depocu"

class KullaniciCreate(KullaniciBase):
    sifre: str

class KullaniciUpdate(BaseModel):
    kullanici_adi: Optional[str] = None
    ad_soyad: Optional[str] = None
    rol: Optional[str] = None
    sifre: Optional[str] = None  # Boş bırakılırsa şifre değişmez

class KullaniciResponse(KullaniciBase):
    id: int
    olusturma_tarihi: datetime

    class Config:
        from_attributes = True


# ========================
# AUTH (KİMLİK DOĞRULAMA) ŞEMALARİ
# ========================

class LoginRequest(BaseModel):
    kullanici_adi: str
    sifre: str

class TokenUserInfo(BaseModel):
    id: int
    kullanici_adi: str
    ad_soyad: str
    rol: str

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
# TEDARİKCİ ŞEMALARİ
# ========================
class TedarikciBase(BaseModel):
    firma_adi: str
    iletisim_kisi: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None

class TedarikciCreate(TedarikciBase):
    pass

class TedarikciUpdate(BaseModel):
    firma_adi: Optional[str] = None
    iletisim_kisi: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[str] = None

class Tedarikci(TedarikciBase):
    id: int

    class Config:
        from_attributes = True
