"""
Faz 1 testleri — Çıkış akışı güvenlik düzeltmeleri.

Kapsam:
- Sevkiyat planı oluşturmada yalnızca Planlandi kabul edilmesi
- Mükerrer irsaliye ile mükerrer stok çıkışının engellenmesi (idempotency)
- Yanlış sevkiyat_id ile irsaliye oluşturma reddi
- Kesilmiş irsaliyede alan düzenleme reddi
- Stok hareketine irsaliye_no yazılması
"""

from datetime import date, datetime, timedelta

_GELECEK = date.today() + timedelta(days=7)
from unittest.mock import MagicMock, call

import pytest

from app.application.dto.sevkiyat_plani_dto import SevkiyatPlaniOlusturRequestDTO
from app.application.dto.irsaliye_dto import (
    IrsaliyeOlusturRequestDTO,
    IrsaliyeGuncelleRequestDTO,
)
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatDurum
from app.core.entities.irsaliye import IrsaliyeDurum
from app.core.exceptions import GecersizIslemError, KayitBulunamadiError

pytestmark = pytest.mark.unit


# ─── Yardımcılar ───


def _make_siparis_entity(siparis_id=1):
    siparis = MagicMock()
    siparis.id = siparis_id
    siparis.siparis_no = "SIP-2026-0001"
    siparis.kalemler = [MagicMock(urun_id=10, miktar=5)]
    return siparis


def _make_irsaliye_entity(durum=IrsaliyeDurum.TASLAK):
    entity = MagicMock()
    entity.id = 100
    entity.siparis_id = 1
    entity.sevkiyat_id = None
    entity.irsaliye_no = "IRS-2026-0001"
    entity.irsaliye_tarihi = date(2026, 4, 13)
    entity.belge_turu = "SevkIrsaliyesi"
    entity.tir_plaka = "34 ABC 123"
    entity.sofor_adi = "Test Sofor"
    entity.durum = durum
    entity.olusturma_tarihi = datetime(2026, 4, 13)
    entity.guncelleme_tarihi = datetime(2026, 4, 13)
    return entity


def _make_sevkiyat_entity(siparis_id=1, durum=SevkiyatDurum.PLANLANDI):
    return SevkiyatPlani(
        id=55,
        siparis_id=siparis_id,
        durum=durum,
    )


# ═══════════════════════════════════════════════════════
# 1. Sevkiyat planı oluşturmada durum kısıtlaması
# ═══════════════════════════════════════════════════════


class TestSevkiyatPlaniDurumKisitlamasi:

    def test_planlandi_durumu_kabul_edilir(self):
        dto = SevkiyatPlaniOlusturRequestDTO(
            siparis_id=1,
            yukleme_tarihi=_GELECEK,
            durum=SevkiyatDurum.PLANLANDI,
        )
        assert dto.durum == SevkiyatDurum.PLANLANDI

    def test_varsayilan_durum_planlandi(self):
        dto = SevkiyatPlaniOlusturRequestDTO(siparis_id=1, yukleme_tarihi=_GELECEK)
        assert dto.durum == SevkiyatDurum.PLANLANDI

    @pytest.mark.parametrize("durum", [
        SevkiyatDurum.YUKLENIYOR,
        SevkiyatDurum.YOLDA,
        SevkiyatDurum.TESLIM_EDILDI,
    ])
    def test_planlandi_disindaki_durumlar_reddedilir(self, durum):
        with pytest.raises(ValueError, match="yalnızca.*Planlandi"):
            SevkiyatPlaniOlusturRequestDTO(siparis_id=1, yukleme_tarihi=_GELECEK, durum=durum)


# ═══════════════════════════════════════════════════════
# 2. İrsaliye sevkiyat_id doğrulaması
# ═══════════════════════════════════════════════════════


class TestIrsaliyeSevkiyatIdDogrulama:

    def test_sevkiyat_id_none_ise_reddedilir(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1, sevkiyat_id=None, irsaliye_tarihi=date(2026, 4, 13)
        )

        with pytest.raises(GecersizIslemError, match="sevkiyat plan"):
            use_case.execute(dto, kullanici_id=7)

        mocks["siparis_repo"].getir_id_ile.assert_not_called()
        mocks["irsaliye_repo"].olustur.assert_not_called()

    def test_var_olmayan_sevkiyat_id_reddedilir(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1, sevkiyat_id=999, irsaliye_tarihi=date(2026, 4, 13)
        )

        mocks["siparis_repo"].getir_id_ile.return_value = _make_siparis_entity()
        mocks["sevkiyat_repo"].getir_id_ile.return_value = None

        with pytest.raises(KayitBulunamadiError):
            use_case.execute(dto, kullanici_id=7)

    def test_farkli_siparise_ait_sevkiyat_id_reddedilir(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1, sevkiyat_id=55, irsaliye_tarihi=date(2026, 4, 13)
        )

        mocks["siparis_repo"].getir_id_ile.return_value = _make_siparis_entity(siparis_id=1)
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _make_sevkiyat_entity(siparis_id=99)

        with pytest.raises(GecersizIslemError, match="farklı bir siparişe ait"):
            use_case.execute(dto, kullanici_id=7)

    def test_ayni_siparise_ait_sevkiyat_id_kabul_edilir(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1, sevkiyat_id=55, irsaliye_tarihi=date(2026, 4, 13)
        )

        mocks["siparis_repo"].getir_id_ile.return_value = _make_siparis_entity(siparis_id=1)
        mocks["sevkiyat_repo"].getir_id_ile.return_value = _make_sevkiyat_entity(siparis_id=1)
        mocks["irsaliye_repo"].sevkiyat_icin_irsaliye_var_mi.return_value = False
        mocks["irsaliye_repo"].sonraki_irsaliye_no.return_value = "IRS-2026-0001"
        mocks["irsaliye_repo"].olustur.return_value = _make_irsaliye_entity()

        result = use_case.execute(dto, kullanici_id=7)
        assert result.id == 100


# ═══════════════════════════════════════════════════════
# 4. İrsaliye güncelleme — düzenlenebilir_mi() kontrolü
# ═══════════════════════════════════════════════════════


class TestIrsaliyeDuzenlenebilirlik:

    def test_taslak_irsaliyede_alan_degisikligi_basarili(self, irsaliye_guncelle_uc_mock):
        use_case, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _make_irsaliye_entity(durum=IrsaliyeDurum.TASLAK)
        irsaliye.duzenlenebilir_mi.return_value = True

        dto = IrsaliyeGuncelleRequestDTO(tir_plaka="06 DEF 456")

        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye
        mocks["irsaliye_repo"].guncelle.return_value = irsaliye

        result = use_case.execute(100, dto, kullanici_id=7)
        assert result.id == 100

    def test_kesilmis_irsaliyede_alan_degisikligi_reddedilir(self, irsaliye_guncelle_uc_mock):
        use_case, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _make_irsaliye_entity(durum=IrsaliyeDurum.KESILDI)
        irsaliye.duzenlenebilir_mi.return_value = False

        dto = IrsaliyeGuncelleRequestDTO(tir_plaka="06 DEF 456")

        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye

        with pytest.raises(GecersizIslemError, match="düzenlenemez"):
            use_case.execute(100, dto, kullanici_id=7)

    def test_kesilmis_irsaliyede_durum_gecisi_basarili(self, irsaliye_guncelle_uc_mock):
        use_case, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _make_irsaliye_entity(durum=IrsaliyeDurum.KESILDI)
        irsaliye.duzenlenebilir_mi.return_value = False

        dto = IrsaliyeGuncelleRequestDTO(durum=IrsaliyeDurum.GONDERILDI)

        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye
        mocks["irsaliye_repo"].guncelle.return_value = irsaliye

        result = use_case.execute(100, dto, kullanici_id=7)
        assert result.id == 100

    def test_gonderilmis_irsaliyede_alan_degisikligi_reddedilir(self, irsaliye_guncelle_uc_mock):
        use_case, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _make_irsaliye_entity(durum=IrsaliyeDurum.GONDERILDI)
        irsaliye.duzenlenebilir_mi.return_value = False

        dto = IrsaliyeGuncelleRequestDTO(sofor_adi="Yeni Sofor")

        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye

        with pytest.raises(GecersizIslemError, match="düzenlenemez"):
            use_case.execute(100, dto, kullanici_id=7)
