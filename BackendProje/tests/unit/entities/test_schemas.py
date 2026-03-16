"""
Unit testler: Pydantic schema validation
DB gerektirmez — sadece schema kurallarını test eder.
"""

import pytest
from pydantic import ValidationError
from schemas import (
    UrunCreate,
    KullaniciCreate,
    PaletCreate,
    RafBase,
    StokHareketiCreate,
    LoginRequest,
)


pytestmark = pytest.mark.unit


class TestUrunCreateSchema:
    """UrunCreate schema validation testleri."""

    def test_gecerli_urun(self):
        urun = UrunCreate(isim="Test Ürün", barkod="1234567890123")
        assert urun.isim == "Test Ürün"
        assert urun.birim == "Adet"
        assert urun.min_stok == 10

    def test_barkod_format_hatasi(self):
        """Barkod sadece 8-14 haneli numerik olmalı."""
        with pytest.raises(ValidationError) as exc_info:
            UrunCreate(isim="Test", barkod="ABC")
        assert "barkod" in str(exc_info.value)

    def test_ean_format_hatasi(self):
        with pytest.raises(ValidationError):
            UrunCreate(isim="Test", ean="12345")  # 8-14 hane olmalı

    def test_gecerli_ean(self):
        urun = UrunCreate(isim="Test", ean="12345678")
        assert urun.ean == "12345678"

    def test_fiyat_negatif_olamaz(self):
        with pytest.raises(ValidationError):
            UrunCreate(isim="Test", fiyat=-5.0)

    def test_ic_adet_sifir_olamaz(self):
        with pytest.raises(ValidationError):
            UrunCreate(isim="Test", ic_adet=0)

    def test_gecersiz_birim(self):
        with pytest.raises(ValidationError):
            UrunCreate(isim="Test", birim="Ton")

    def test_gecerli_birimler(self):
        for birim in ["Adet", "Kg", "Metre", "Kutu", "Litre", "Paket"]:
            urun = UrunCreate(isim="Test", birim=birim)
            assert urun.birim == birim


class TestKullaniciCreateSchema:
    """KullaniciCreate schema validation testleri."""

    def test_gecerli_kullanici(self):
        k = KullaniciCreate(
            kullanici_adi="testuser",
            ad_soyad="Test User",
            sifre="Test1234",
        )
        assert k.rol == "depocu"  # varsayılan rol

    def test_sifre_cok_kisa(self):
        with pytest.raises(ValidationError):
            KullaniciCreate(
                kullanici_adi="testuser",
                ad_soyad="Test",
                sifre="Ab1",  # min 8 karakter
            )

    def test_sifre_buyuk_harf_yok(self):
        with pytest.raises(ValidationError) as exc_info:
            KullaniciCreate(
                kullanici_adi="testuser",
                ad_soyad="Test",
                sifre="test1234",  # büyük harf yok
            )
        assert "büyük harf" in str(exc_info.value)

    def test_sifre_kucuk_harf_yok(self):
        with pytest.raises(ValidationError):
            KullaniciCreate(
                kullanici_adi="testuser",
                ad_soyad="Test",
                sifre="TEST1234",
            )

    def test_sifre_rakam_yok(self):
        with pytest.raises(ValidationError):
            KullaniciCreate(
                kullanici_adi="testuser",
                ad_soyad="Test",
                sifre="TestTest",
            )

    def test_gecersiz_rol(self):
        with pytest.raises(ValidationError):
            KullaniciCreate(
                kullanici_adi="testuser",
                ad_soyad="Test",
                sifre="Test1234",
                rol="superadmin",
            )

    def test_gecerli_roller(self):
        for rol in ["admin", "depocu", "goruntuleyen", "lojistik"]:
            k = KullaniciCreate(
                kullanici_adi=f"user_{rol}",
                ad_soyad="Test",
                sifre="Test1234",
                rol=rol,
            )
            assert k.rol == rol


class TestPaletCreateSchema:
    """PaletCreate schema validation testleri."""

    def test_koli_adedi_pozitif_olmali(self):
        with pytest.raises(ValidationError):
            PaletCreate(lot_id=1, palet_no="PLT-001", koli_adedi=0)

    def test_koli_adedi_negatif_olamaz(self):
        with pytest.raises(ValidationError):
            PaletCreate(lot_id=1, palet_no="PLT-001", koli_adedi=-5)

    def test_gecerli_palet(self):
        p = PaletCreate(lot_id=1, palet_no="PLT-001", koli_adedi=10)
        assert p.koli_adedi == 10


class TestRafBaseSchema:
    """RafBase schema validation testleri."""

    def test_kapasite_pozitif_olmali(self):
        with pytest.raises(ValidationError):
            RafBase(kod="A-01", kapasite=0)

    def test_gecerli_raf(self):
        r = RafBase(kod="A-01", kapasite=50)
        assert r.kapasite == 50
        assert r.bolge == ""


class TestStokHareketiSchema:
    """StokHareketiCreate schema validation testleri."""

    def test_gecerli_giris(self):
        sh = StokHareketiCreate(urun_id=1, hareket_tipi="giris", miktar=100)
        assert sh.hareket_tipi == "giris"

    def test_gecerli_cikis(self):
        sh = StokHareketiCreate(urun_id=1, hareket_tipi="cikis", miktar=50)
        assert sh.hareket_tipi == "cikis"

    def test_gecersiz_hareket_tipi(self):
        with pytest.raises(ValidationError):
            StokHareketiCreate(urun_id=1, hareket_tipi="transfer", miktar=10)


class TestLoginRequestSchema:
    """LoginRequest schema validation testleri."""

    def test_kullanici_adi_cok_kisa(self):
        with pytest.raises(ValidationError):
            LoginRequest(kullanici_adi="ab", sifre="test")

    def test_gecerli_login(self):
        lr = LoginRequest(kullanici_adi="admin", sifre="1234")
        assert lr.kullanici_adi == "admin"
