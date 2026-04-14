"""
Unit testler: DTO katmanı sınır değeri validasyonları.

DB gerektirmez — yalnızca Pydantic kurallarını doğrular.
Kapsam: boş string, sıfır/negatif sayısal, max_length aşımı,
NULL FK (id=0/-1), model_validator kombinasyonları.
"""

import pytest
from datetime import date, timedelta
from pydantic import ValidationError

from app.application.dto.urun_dto import UrunOlusturRequestDTO
from app.application.dto.siparis_dto import (
    SiparisOlusturRequestDTO,
    SiparisKalemiOlusturRequestDTO,
)
from app.application.dto.stok_hareketi_dto import StokHareketiOlusturRequestDTO
from app.application.dto.sevkiyat_plani_dto import SevkiyatPlaniOlusturRequestDTO

pytestmark = pytest.mark.unit

_GELECEK = date.today() + timedelta(days=7)


# ══════════════════════════════════════════
# URUN DTO
# ══════════════════════════════════════════

class TestUrunDTOSinirDegerleri:
    """UrunOlusturRequestDTO sınır değeri testleri."""

    @pytest.mark.parametrize("isim", ["", "   ", "\t", "\n  \t"])
    def test_bos_veya_bosluklu_isim(self, isim):
        """Boş veya sadece boşluktan oluşan isim geçersiz."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim=isim)

    def test_isim_max_uzunluk_asimi(self):
        """201 karakterlik isim 200 sınırını aşar."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="x" * 201)

    def test_aciklama_max_uzunluk_asimi(self):
        """2001 karakterlik açıklama 2000 sınırını aşar."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", aciklama="x" * 2001)

    @pytest.mark.parametrize("ic_adet", [0, -1, -100])
    def test_ic_adet_sifir_veya_negatif(self, ic_adet):
        """ic_adet ge=1 kuralı: 0 ve negatif geçersiz."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", ic_adet=ic_adet)

    @pytest.mark.parametrize("fiyat", [-0.01, -1.0, -999.99])
    def test_fiyat_negatif(self, fiyat):
        """fiyat ge=0: negatif değer geçersiz."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", fiyat=fiyat)

    def test_min_stok_negatif(self):
        """min_stok ge=0: negatif değer geçersiz."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", min_stok=-1)

    @pytest.mark.parametrize("marka_id", [0, -1])
    def test_marka_id_sifir_veya_negatif(self, marka_id):
        """marka_id gt=0: 0 ve negatif geçersiz (NULL FK koruması)."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", marka_id=marka_id)

    @pytest.mark.parametrize("kategori_id", [0, -5])
    def test_kategori_id_sifir_veya_negatif(self, kategori_id):
        """kategori_id gt=0: 0 ve negatif geçersiz."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", kategori_id=kategori_id)

    def test_gecersiz_birim(self):
        """İzin verilmeyen birim değeri geçersiz."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", birim="Ton")

    @pytest.mark.parametrize("ean", [
        "1234567",           # 7 hane — çok kısa
        "123456789012345",   # 15 hane — çok uzun
        "ABCDEFGH",          # harf içeriyor
        "1234-5678-9012-345", # normalize edilse bile 15 hane — geçersiz
    ])
    def test_ean_gecersiz_format(self, ean):
        """Geçersiz EAN formatı ValidationError fırlatmalı."""
        with pytest.raises(ValidationError):
            UrunOlusturRequestDTO(isim="Test", ean=ean)

    @pytest.mark.parametrize("birim", ["Adet", "Kg", "Metre", "Kutu", "Litre", "Paket"])
    def test_gecerli_birimler(self, birim):
        """Tüm izinli birim değerleri kabul edilmeli."""
        dto = UrunOlusturRequestDTO(isim="Test", birim=birim)
        assert dto.birim == birim

    def test_opsiyonel_alanlar_none_gecerli(self):
        """Opsiyonel FK alanları None olabilir."""
        dto = UrunOlusturRequestDTO(isim="Test Ürün")
        assert dto.barkod is None
        assert dto.ean is None
        assert dto.marka_id is None
        assert dto.kategori_id is None


# ══════════════════════════════════════════
# SİPARİŞ DTO
# ══════════════════════════════════════════

class TestSiparisDTOSinirDegerleri:
    """SiparisOlusturRequestDTO ve SiparisKalemiOlusturRequestDTO testleri."""

    def _kalem(self, urun_id=1, miktar=5, birim_fiyat=10.0, kdv_orani=18.0):
        return SiparisKalemiOlusturRequestDTO(
            urun_id=urun_id,
            miktar=miktar,
            birim_fiyat=birim_fiyat,
            kdv_orani=kdv_orani,
        )

    def _gecerli_siparis(self, **overrides):
        base = dict(
            musteri_adi="Test Müşteri",
            teslimat_adresi="Test Adres, İstanbul",
            teslimat_tarihi=_GELECEK,
            kalemler=[self._kalem()],
        )
        base.update(overrides)
        return SiparisOlusturRequestDTO(**base)

    @pytest.mark.parametrize("musteri_adi", ["", "   "])
    def test_musteri_adi_bos(self, musteri_adi):
        """Boş/boşluklu müşteri adı geçersiz."""
        with pytest.raises(ValidationError):
            self._gecerli_siparis(musteri_adi=musteri_adi)

    def test_musteri_adi_max_uzunluk_asimi(self):
        """201 karakterlik müşteri adı geçersiz."""
        with pytest.raises(ValidationError):
            self._gecerli_siparis(musteri_adi="x" * 201)

    def test_teslimat_adresi_max_uzunluk_asimi(self):
        """501 karakterlik adres geçersiz."""
        with pytest.raises(ValidationError):
            self._gecerli_siparis(teslimat_adresi="x" * 501)

    def test_bos_kalemler_listesi(self):
        """En az 1 kalem zorunlu."""
        with pytest.raises(ValidationError):
            self._gecerli_siparis(kalemler=[])

    def test_duplicate_urun_id_ayni_siparis(self):
        """Aynı ürün birden fazla kalemde yer alamaz."""
        with pytest.raises(ValidationError):
            self._gecerli_siparis(kalemler=[
                self._kalem(urun_id=1),
                self._kalem(urun_id=1),
            ])

    def test_gecmis_teslimat_tarihi(self):
        """Geçmiş tarihli teslimat geçersiz."""
        with pytest.raises(ValidationError):
            self._gecerli_siparis(teslimat_tarihi=date.today() - timedelta(days=1))

    @pytest.mark.parametrize("miktar", [0, -1])
    def test_kalem_miktar_sifir_veya_negatif(self, miktar):
        """Kalem miktarı gt=0: sıfır ve negatif geçersiz."""
        with pytest.raises(ValidationError):
            self._kalem(miktar=miktar)

    @pytest.mark.parametrize("birim_fiyat", [-0.01, -100.0])
    def test_kalem_birim_fiyat_negatif(self, birim_fiyat):
        """Birim fiyat ge=0: negatif geçersiz."""
        with pytest.raises(ValidationError):
            self._kalem(birim_fiyat=birim_fiyat)

    @pytest.mark.parametrize("kdv", [-0.01, 100.01, 200.0])
    def test_kalem_kdv_orani_sinir_disi(self, kdv):
        """KDV oranı 0–100 aralığında olmalı."""
        with pytest.raises(ValidationError):
            self._kalem(kdv_orani=kdv)

    @pytest.mark.parametrize("urun_id", [0, -1])
    def test_kalem_urun_id_sifir_veya_negatif(self, urun_id):
        """urun_id gt=0: 0 ve negatif geçersiz (NULL FK koruması)."""
        with pytest.raises(ValidationError):
            self._kalem(urun_id=urun_id)

    def test_farkli_urun_idler_gecerli(self):
        """Farklı ürün ID'leri olan iki kalem kabul edilmeli."""
        siparis = self._gecerli_siparis(kalemler=[
            self._kalem(urun_id=1),
            self._kalem(urun_id=2),
        ])
        assert len(siparis.kalemler) == 2


# ══════════════════════════════════════════
# STOK HAREKETİ DTO
# ══════════════════════════════════════════

class TestStokHareketiDTOSinirDegerleri:
    """StokHareketiOlusturRequestDTO sınır değeri testleri."""

    @pytest.mark.parametrize("miktar", [0, -1, -50])
    def test_miktar_sifir_veya_negatif(self, miktar):
        """Miktar gt=0: sıfır ve negatif geçersiz."""
        with pytest.raises(ValidationError):
            StokHareketiOlusturRequestDTO(
                urun_id=1, hareket_tipi="giris", miktar=miktar
            )

    @pytest.mark.parametrize("urun_id", [0, -1])
    def test_urun_id_sifir_veya_negatif(self, urun_id):
        """urun_id gt=0: 0 ve negatif geçersiz."""
        with pytest.raises(ValidationError):
            StokHareketiOlusturRequestDTO(
                urun_id=urun_id, hareket_tipi="giris", miktar=10
            )

    def test_gecersiz_hareket_tipi(self):
        """Yalnızca 'giris' ve 'cikis' kabul edilir."""
        with pytest.raises(ValidationError):
            StokHareketiOlusturRequestDTO(
                urun_id=1, hareket_tipi="transfer", miktar=10
            )

    def test_cikis_siparis_no_ve_aciklama_yok(self):
        """Çıkış hareketi; siparis_no veya aciklama zorunlu."""
        with pytest.raises(ValidationError):
            StokHareketiOlusturRequestDTO(
                urun_id=1,
                hareket_tipi="cikis",
                miktar=10,
                # siparis_no=None (varsayılan), aciklama="" (varsayılan) → hata
            )

    def test_cikis_aciklama_ile_gecerli(self):
        """Çıkış hareketi; açıklama varsa geçerli."""
        dto = StokHareketiOlusturRequestDTO(
            urun_id=1, hareket_tipi="cikis", miktar=10, aciklama="Sayım düzeltmesi"
        )
        assert dto.hareket_tipi == "cikis"

    def test_cikis_siparis_no_ile_gecerli(self):
        """Çıkış hareketi; sipariş no varsa geçerli."""
        dto = StokHareketiOlusturRequestDTO(
            urun_id=1, hareket_tipi="cikis", miktar=10, siparis_no="SIP-2026-0001"
        )
        assert dto.siparis_no == "SIP-2026-0001"

    def test_barkod_51_karakter_gecersiz(self):
        """51 karakterlik barkod max 50 sınırını aşar."""
        with pytest.raises(ValidationError):
            StokHareketiOlusturRequestDTO(
                urun_id=1, hareket_tipi="giris", miktar=5,
                barkodlar=["x" * 51],
            )

    def test_barkod_50_karakter_gecerli(self):
        """50 karakterlik barkod sınırda kabul edilmeli."""
        dto = StokHareketiOlusturRequestDTO(
            urun_id=1, hareket_tipi="giris", miktar=5,
            barkodlar=["x" * 50],
        )
        assert len(dto.barkodlar[0]) == 50


# ══════════════════════════════════════════
# SEVKİYAT PLANI DTO
# ══════════════════════════════════════════

class TestSevkiyatDTOSinirDegerleri:
    """SevkiyatPlaniOlusturRequestDTO sınır değeri testleri."""

    @pytest.mark.parametrize("siparis_id", [0, -1])
    def test_siparis_id_sifir_veya_negatif(self, siparis_id):
        """siparis_id gt=0: 0 ve negatif geçersiz (NULL FK koruması)."""
        with pytest.raises(ValidationError):
            SevkiyatPlaniOlusturRequestDTO(siparis_id=siparis_id)

    def test_gecersiz_durum_degeri(self):
        """Enum dışı durum değeri geçersiz."""
        with pytest.raises(ValidationError):
            SevkiyatPlaniOlusturRequestDTO(siparis_id=1, durum="GecersizDurum")

    def test_tir_plaka_max_uzunluk_asimi(self):
        """21 karakterlik TIR plakası 20 sınırını aşar."""
        with pytest.raises(ValidationError):
            SevkiyatPlaniOlusturRequestDTO(siparis_id=1, tir_plaka="x" * 21)

    def test_notlar_max_uzunluk_asimi(self):
        """2001 karakterlik notlar alanı geçersiz."""
        with pytest.raises(ValidationError):
            SevkiyatPlaniOlusturRequestDTO(siparis_id=1, notlar="x" * 2001)

    def test_yalnizca_planlandi_durumu_kabul_edilir(self):
        """Oluşturmada yalnızca Planlandi durumu kabul edilmeli."""
        dto = SevkiyatPlaniOlusturRequestDTO(siparis_id=1, yukleme_tarihi=_GELECEK, durum="Planlandi")
        assert dto.durum == "Planlandi"

    @pytest.mark.parametrize("durum", ["Yukleniyor", "Yolda", "TeslimEdildi"])
    def test_planlandi_disindaki_durumlar_reddedilir(self, durum):
        """Oluşturmada Planlandi dışındaki durumlar reddedilmeli."""
        with pytest.raises(ValidationError):
            SevkiyatPlaniOlusturRequestDTO(siparis_id=1, durum=durum)

    def test_opsiyonel_alanlar_none_gecerli(self):
        """Opsiyonel alanların hepsi None olabilir."""
        dto = SevkiyatPlaniOlusturRequestDTO(siparis_id=1, yukleme_tarihi=_GELECEK)
        assert dto.tir_plaka is None
        assert dto.sofor_adi is None
        assert dto.yukleme_tarihi == _GELECEK
