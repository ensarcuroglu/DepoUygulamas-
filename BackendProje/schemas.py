from pydantic import BaseModel, ConfigDict, Field, field_validator, EmailStr
from typing import Optional, List, Literal
from datetime import datetime, date
import re


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    aktif: bool
    olusturma_tarihi: datetime


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    aktif: bool
    olusturma_tarihi: datetime


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    aktif: bool
    olusturma_tarihi: datetime


# ========================
# RAF ŞEMALARİ
# ========================

class RafBase(BaseModel):
    depo_id: Optional[int] = None
    kod: str
    bolge: Optional[str] = ""
    kapasite: Optional[int] = Field(100, gt=0, description="Kapasite pozitif olmalı")

class RafCreate(RafBase):
    pass

class RafUpdate(BaseModel):
    depo_id: Optional[int] = None
    kod: Optional[str] = None
    bolge: Optional[str] = None
    kapasite: Optional[int] = None
    aktif: Optional[bool] = None

class RafResponse(RafBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aktif: bool
    depo: Optional[DepoResponse] = None
    olusturma_tarihi: datetime


# ========================
# TEDARİKÇİ ŞEMALARİ
# ========================

class TedarikciBase(BaseModel):
    firma_adi: str
    iletisim_kisi: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[EmailStr] = None
    adres: Optional[str] = None
    vergi_no: Optional[str] = None

class TedarikciCreate(TedarikciBase):
    pass

class TedarikciUpdate(BaseModel):
    firma_adi: Optional[str] = None
    iletisim_kisi: Optional[str] = None
    telefon: Optional[str] = None
    email: Optional[EmailStr] = None
    adres: Optional[str] = None
    vergi_no: Optional[str] = None
    aktif: Optional[bool] = None

class TedarikciResponse(TedarikciBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aktif: bool
    olusturma_tarihi: datetime


# ========================
# ÜRÜN ŞEMALARİ
# ========================

class UrunBase(BaseModel):
    isim: str
    marka_id: Optional[int] = None
    kategori_id: Optional[int] = None
    tedarikci_id: Optional[int] = None
    ean: Optional[str] = Field(None, pattern=r"^\d{8,14}$", description="EAN-8, EAN-13 veya EAN-14")
    barkod: Optional[str] = Field(None, pattern=r"^\d{8,14}$", description="Barkod (numerik)")
    ic_adet: Optional[int] = Field(1, ge=1)
    gramaj: Optional[float] = None
    birim: Optional[Literal["Adet", "Kg", "Metre", "Kutu", "Litre", "Paket"]] = "Adet"
    fiyat: Optional[float] = Field(0.0, ge=0)
    min_stok: Optional[int] = 10
    aciklama: Optional[str] = ""

class UrunCreate(UrunBase):
    pass

class UrunUpdate(BaseModel):
    isim: Optional[str] = None
    marka_id: Optional[int] = None
    kategori_id: Optional[int] = None
    tedarikci_id: Optional[int] = None
    ean: Optional[str] = Field(None, pattern=r"^\d{8,14}$")
    barkod: Optional[str] = Field(None, pattern=r"^\d{8,14}$")
    ic_adet: Optional[int] = Field(None, ge=1)
    gramaj: Optional[float] = None
    birim: Optional[Literal["Adet", "Kg", "Metre", "Kutu", "Litre", "Paket"]] = None
    fiyat: Optional[float] = Field(None, ge=0)
    min_stok: Optional[int] = None
    aciklama: Optional[str] = None
    aktif: Optional[bool] = None

class UrunResponse(UrunBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    stok_miktari: int
    durum: str
    aktif: bool
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    marka: Optional[MarkaResponse] = None
    kategori: Optional[KategoriResponse] = None
    tedarikci: Optional[TedarikciResponse] = None

class UrunListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

    id: int
    aktif: bool
    olusturma_tarihi: datetime

class LotDetailResponse(LotResponse):
    urun: Optional[UrunListResponse] = None


# ========================
# PALET ŞEMALARİ
# ========================

class PaletBase(BaseModel):
    lot_id: int
    raf_id: Optional[int] = None
    palet_no: str
    koli_adedi: int = Field(..., gt=0, description="Koli adedi pozitif olmalı")
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None

class PaletCreate(PaletBase):
    pass

class PaletUpdate(BaseModel):
    raf_id: Optional[int] = None
    koli_adedi: Optional[int] = Field(None, gt=0)
    palet_kg: Optional[float] = None
    vardiya: Optional[str] = None
    aktif: Optional[bool] = None

class PaletResponse(PaletBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tarih: datetime
    aktif: bool
    olusturma_tarihi: datetime

class PaletDetailResponse(PaletResponse):
    lot: Optional[LotResponse] = None
    raf: Optional[RafResponse] = None


# ========================
# STOK HAREKETİ ŞEMALARİ
# ========================

class StokHareketiBase(BaseModel):
    urun_id: int
    lot_id: Optional[int] = None
    palet_id: Optional[int] = None
    raf_id: Optional[int] = None
    hareket_tipi: Literal["giris", "cikis"]
    miktar: int
    siparis_no: Optional[str] = None
    tir_plaka: Optional[str] = None
    depo_kapi: Optional[str] = None
    barkodlar: Optional[List[str]] = None
    aciklama: Optional[str] = ""

class StokHareketiCreate(StokHareketiBase):
    pass

class StokHareketiResponse(StokHareketiBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kullanici_id: Optional[int] = None
    kullanici: Optional["KullaniciResponse"] = None
    raf: Optional[RafResponse] = None
    tarih: datetime


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    tarih: datetime
    kullanici_ad_soyad: Optional[str] = None


# ========================
# KULLANICI ŞEMALARİ
# ========================

class KullaniciBase(BaseModel):
    kullanici_adi: str
    ad_soyad: str
    rol: Literal["admin", "depocu", "goruntuleyen", "lojistik"] = "depocu"
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None
    depo_id: Optional[int] = None

class KullaniciCreate(KullaniciBase):
    sifre: str = Field(..., min_length=8, max_length=128)

    @field_validator("sifre")
    @classmethod
    def sifre_kompliksitesi(cls, v: str) -> str:
        """Şifre en az 1 büyük harf, 1 küçük harf, 1 rakam içermeli."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Şifre en az bir büyük harf içermeli.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Şifre en az bir küçük harf içermeli.")
        if not re.search(r"\d", v):
            raise ValueError("Şifre en az bir rakam içermeli.")
        return v

class KullaniciUpdate(BaseModel):
    kullanici_adi: Optional[str] = None
    ad_soyad: Optional[str] = None
    rol: Optional[Literal["admin", "depocu", "goruntuleyen", "lojistik"]] = None
    sifre: Optional[str] = Field(None, min_length=8, max_length=128)
    telefon: Optional[str] = None
    email: Optional[str] = None
    departman: Optional[str] = None
    sicil_no: Optional[str] = None
    kart_numarasi: Optional[str] = None
    depo_id: Optional[int] = None

    @field_validator("sifre")
    @classmethod
    def sifre_kompliksitesi(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not re.search(r"[A-Z]", v):
                raise ValueError("Şifre en az bir büyük harf içermeli.")
            if not re.search(r"[a-z]", v):
                raise ValueError("Şifre en az bir küçük harf içermeli.")
            if not re.search(r"\d", v):
                raise ValueError("Şifre en az bir rakam içermeli.")
        return v

class KullaniciResponse(KullaniciBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    olusturma_tarihi: datetime


# ========================
# AUTH ŞEMALARİ
# ========================

class LoginRequest(BaseModel):
    kullanici_adi: str = Field(..., min_length=3, max_length=50)
    sifre: str = Field(..., min_length=1, max_length=128)

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
    konu: str = Field(..., max_length=200)
    kategori: Literal["Teknik", "Stok", "Sistem", "Diger"]
    oncelik: Literal["Normal", "Yüksek", "Düşük"] = "Normal"
    aciklama: str = Field(..., max_length=5000)

class DestekTalebiCreate(DestekTalebiBase):
    pass

class DestekTalebiUpdate(BaseModel):
    durum: Optional[Literal["Acik", "Islemde", "Kapalı"]] = None
    admin_cevabi: Optional[str] = Field(None, max_length=5000)
    oncelik: Optional[Literal["Normal", "Yüksek", "Düşük"]] = None

class DestekTalebiResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kullanici_id: int
    konu: str
    kategori: str
    oncelik: str
    aciklama: str
    durum: str
    admin_cevabi: Optional[str] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    kullanici: Optional[KullaniciResponse] = None


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    siparis_id: int
    urun: Optional[UrunListResponse] = None

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
    model_config = ConfigDict(from_attributes=True)

    id: int
    siparis_no: str
    olusturan_kullanici_id: Optional[int] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    aktif: bool

class SiparisDetayResponse(SiparisResponse):
    kalemler: List[SiparisKalemiResponse] = []


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
    cikis_saati: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    varis_saati: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    durum: Optional[Literal["Planlandi", "Yukleniyor", "Tamamlandi", "Iptal"]] = "Planlandi"
    notlar: Optional[str] = ""

class SevkiyatPlaniCreate(SevkiyatPlaniBase):
    pass

class SevkiyatPlaniUpdate(BaseModel):
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    sofor_telefon: Optional[str] = None
    depo_kapi: Optional[str] = None
    yukleme_tarihi: Optional[date] = None
    cikis_saati: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    varis_saati: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    durum: Optional[Literal["Planlandi", "Yukleniyor", "Tamamlandi", "Iptal"]] = None
    notlar: Optional[str] = None

class SevkiyatPlaniResponse(SevkiyatPlaniBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    siparis: Optional[SiparisResponse] = None


# ========================
# İRSALİYE ŞEMALARİ
# ========================

class IrsaliyeBase(BaseModel):
    siparis_id: int
    sevkiyat_id: Optional[int] = None
    irsaliye_tarihi: date
    belge_turu: Optional[Literal["SevkIrsaliyesi", "AlimIrsaliyesi"]] = "SevkIrsaliyesi"
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: Optional[Literal["Taslak", "Kesildi", "Gonderildi"]] = "Taslak"

class IrsaliyeCreate(IrsaliyeBase):
    pass

class IrsaliyeUpdate(BaseModel):
    belge_turu: Optional[Literal["SevkIrsaliyesi", "AlimIrsaliyesi"]] = None
    tir_plaka: Optional[str] = None
    sofor_adi: Optional[str] = None
    durum: Optional[Literal["Taslak", "Kesildi", "Gonderildi"]] = None

class IrsaliyeResponse(IrsaliyeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    irsaliye_no: str
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime
    siparis: Optional[SiparisResponse] = None


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_aktif: bool
    olusturan_kullanici_id: Optional[int] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    kullanici_id: int
    olusturma_tarihi: datetime
    tamamlanma_tarihi: Optional[datetime] = None


# ========================
# RAPOR ZAMANLAMA ŞEMALARİ
# ========================

class RaporScheduleBase(BaseModel):
    sablon_id: int
    sablon_adi: str
    periyod: Literal["gunluk", "haftalik", "aylik"]
    saat: str = Field(..., pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    alici_emailler: Optional[List[EmailStr]] = None
    format: Optional[Literal["pdf", "excel"]] = "pdf"

class RaporScheduleCreate(RaporScheduleBase):
    pass

class RaporScheduleUpdate(BaseModel):
    sablon_adi: Optional[str] = None
    periyod: Optional[Literal["gunluk", "haftalik", "aylik"]] = None
    saat: Optional[str] = Field(None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    alici_emailler: Optional[List[EmailStr]] = None
    format: Optional[Literal["pdf", "excel"]] = None
    is_aktif: Optional[bool] = None

class RaporScheduleResponse(RaporScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_aktif: bool
    son_calistirilma: Optional[datetime] = None
    olusturma_tarihi: datetime
    guncelleme_tarihi: datetime


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
    model_config = ConfigDict(from_attributes=True)

    id: int
    sayim_id: int
    user_id: Optional[int] = None
    sayim_tarihi: datetime
    urun_adi: Optional[str] = None

class StokSayimCreate(BaseModel):
    aciklama: Optional[str] = ""

class StokSayimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


# Forward reference çözümlemesi (StokHareketiResponse -> KullaniciResponse)
StokHareketiResponse.model_rebuild()
