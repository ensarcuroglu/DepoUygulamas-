"""
Faz 4 testleri — Veri doğrulama ve yetki sıkılaştırma.

Kapsam:
- Saat regex (HH:MM) doğrulaması
- Zorunlu yukleme_tarihi (SevkiyatPlani) ve irsaliye_tarihi (İrsaliye)
- Sipariş SiparisGuncelleRequestDTO aktif alanı kaldırılmıştır
- Sevkiyat durum-bazlı meta alan kilitleri (YOLDA / TESLIM_EDILDI)
- Sipariş durum-bazlı teslimat meta kilidi (YOLA_CIKTI / TESLIM_EDILDI / IPTAL)
"""

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.application.dto.sevkiyat_plani_dto import (
    SevkiyatPlaniOlusturRequestDTO,
    SevkiyatPlaniGuncelleRequestDTO,
)
from app.application.dto.irsaliye_dto import IrsaliyeOlusturRequestDTO
from app.application.dto.siparis_dto import SiparisGuncelleRequestDTO
from app.core.entities.siparis import Siparis, SiparisDurum
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatDurum
from app.core.exceptions import GecersizIslemError

pytestmark = pytest.mark.unit

_GELECEK = date.today() + timedelta(days=7)


# ═══════════════════════════════════════════════════════
# 1. Saat formatı doğrulaması (HH:MM 24h)
# ═══════════════════════════════════════════════════════


class TestSaatRegexDogrulama:

    @pytest.mark.parametrize("saat", ["00:00", "09:30", "13:45", "23:59"])
    def test_gecerli_saatler_kabul_edilir(self, saat):
        dto = SevkiyatPlaniOlusturRequestDTO(
            siparis_id=1, yukleme_tarihi=_GELECEK, cikis_saati=saat, varis_saati=saat
        )
        assert dto.cikis_saati == saat
        assert dto.varis_saati == saat

    @pytest.mark.parametrize("saat", ["24:00", "9:30", "12:60", "abc", "12-30", "12:5"])
    def test_gecersiz_saatler_reddedilir(self, saat):
        with pytest.raises(ValidationError):
            SevkiyatPlaniOlusturRequestDTO(
                siparis_id=1, yukleme_tarihi=_GELECEK, cikis_saati=saat
            )

    def test_none_ve_bos_saat_kabul_edilir(self):
        dto = SevkiyatPlaniGuncelleRequestDTO(cikis_saati=None, varis_saati="")
        assert dto.cikis_saati is None
        assert dto.varis_saati == ""


# ═══════════════════════════════════════════════════════
# 2. Zorunlu tarihler
# ═══════════════════════════════════════════════════════


class TestZorunluTarihler:

    def test_yukleme_tarihi_zorunlu(self):
        with pytest.raises(ValidationError):
            SevkiyatPlaniOlusturRequestDTO(siparis_id=1)

    def test_irsaliye_tarihi_zorunlu(self):
        with pytest.raises(ValidationError):
            IrsaliyeOlusturRequestDTO(siparis_id=1, sevkiyat_id=55)


# ═══════════════════════════════════════════════════════
# 3. SiparisGuncelleRequestDTO — aktif alanı kaldırıldı
# ═══════════════════════════════════════════════════════


class TestSiparisGuncelleAktifAlaniKaldirildi:

    def test_aktif_alani_artik_yok(self):
        # aktif=False verilse bile modele geçmez (extra alan göz ardı edilir veya hata).
        dto = SiparisGuncelleRequestDTO(notlar="deneme")
        assert not hasattr(dto, "aktif")


# ═══════════════════════════════════════════════════════
# 4. Sevkiyat durum-bazlı meta alan kilitleri
# ═══════════════════════════════════════════════════════


def _sevkiyat(durum=SevkiyatDurum.PLANLANDI):
    return SevkiyatPlani(id=55, siparis_id=1, durum=durum)


class TestSevkiyatMetaKilitleri:

    def test_yolda_iken_tir_plaka_degisimi_reddedilir(self, sevkiyat_guncelle_uc_mock):
        uc, mocks = sevkiyat_guncelle_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat(SevkiyatDurum.YOLDA)
        dto = SevkiyatPlaniGuncelleRequestDTO(tir_plaka="34 XYZ 999")

        with pytest.raises(GecersizIslemError, match="plaka"):
            uc.execute(55, dto, kullanici_id=7)

    def test_yolda_iken_notlar_serbest(self, sevkiyat_guncelle_uc_mock):
        uc, mocks = sevkiyat_guncelle_uc_mock
        plan = _sevkiyat(SevkiyatDurum.YOLDA)
        mocks["sevkiyat_repo"].getir_id_ile.return_value = plan
        mocks["sevkiyat_repo"].guncelle.return_value = plan

        dto = SevkiyatPlaniGuncelleRequestDTO(notlar="Trafik nedeniyle gecikme")
        uc.execute(55, dto, kullanici_id=7)  # hata fırlatmamalı
        assert plan.notlar == "Trafik nedeniyle gecikme"

    def test_teslim_edildi_iken_hicbir_alan_degismez(self, sevkiyat_guncelle_uc_mock):
        uc, mocks = sevkiyat_guncelle_uc_mock
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _sevkiyat(
            SevkiyatDurum.TESLIM_EDILDI
        )
        dto = SevkiyatPlaniGuncelleRequestDTO(notlar="geç not")

        with pytest.raises(GecersizIslemError, match="Teslim"):
            uc.execute(55, dto, kullanici_id=7)


# ═══════════════════════════════════════════════════════
# 5. Sipariş teslimat meta kilitleri
# ═══════════════════════════════════════════════════════


def _siparis(durum=SiparisDurum.BEKLEME):
    return Siparis(
        id=1,
        siparis_no="SIP-2026-0001",
        musteri_adi="Eski Müşteri",
        teslimat_adresi="Eski Adres",
        teslimat_tarihi=_GELECEK,
        durum=durum,
    )


class TestSiparisTeslimatMetaKilidi:

    def test_yola_cikti_iken_teslimat_adresi_degisimi_reddedilir(
        self, siparis_guncelle_uc_mock
    ):
        uc, mocks = siparis_guncelle_uc_mock
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis(
            SiparisDurum.YOLA_CIKTI
        )
        dto = SiparisGuncelleRequestDTO(teslimat_adresi="Yeni Adres")

        with pytest.raises(GecersizIslemError, match="teslimat"):
            uc.execute(1, dto, kullanici_id=7)

    def test_yola_cikti_iken_notlar_serbest(self, siparis_guncelle_uc_mock):
        uc, mocks = siparis_guncelle_uc_mock
        siparis = _siparis(SiparisDurum.YOLA_CIKTI)
        mocks["siparis_repo"].getir_id_ile.return_value = siparis
        mocks["siparis_repo"].guncelle.return_value = siparis

        dto = SiparisGuncelleRequestDTO(notlar="iç not")
        uc.execute(1, dto, kullanici_id=7)  # hata fırlatmamalı
        assert siparis.notlar == "iç not"

    def test_bekleme_iken_teslimat_meta_serbest(self, siparis_guncelle_uc_mock):
        uc, mocks = siparis_guncelle_uc_mock
        siparis = _siparis(SiparisDurum.BEKLEME)
        mocks["siparis_repo"].getir_id_ile.return_value = siparis
        mocks["siparis_repo"].guncelle.return_value = siparis

        dto = SiparisGuncelleRequestDTO(
            musteri_adi="Yeni Müşteri",
            teslimat_adresi="Yeni Adres",
            teslimat_tarihi=_GELECEK,
        )
        uc.execute(1, dto, kullanici_id=7)
        assert siparis.musteri_adi == "Yeni Müşteri"
        assert siparis.teslimat_adresi == "Yeni Adres"
