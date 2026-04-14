"""
Unit testler: Yükleme onayı transaction atomikligi.

Faz 2 sonrası:
- IrsaliyeOlusturUseCase sadece evrak kaydı (transaction yok).
- Stok çıkışı + durum geçişi yalnızca YuklemeOnaylaUseCase'de.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.application.dto.sevkiyat_plani_dto import SevkiyatPlaniGuncelleRequestDTO
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatDurum
from app.core.exceptions import GecersizIslemError, StokVeriUyumsuzluguError

pytestmark = pytest.mark.unit


def _make_siparis_entity():
    siparis = MagicMock()
    siparis.id = 1
    siparis.siparis_no = "SIP-2026-0001"
    kalem = MagicMock()
    kalem.id = 101
    kalem.urun_id = 10
    kalem.miktar = 5
    siparis.kalemler = [kalem]
    return siparis


def _make_sevkiyat_entity(durum=SevkiyatDurum.PLANLANDI):
    return SevkiyatPlani(
        id=55,
        siparis_id=1,
        tir_plaka="34 XYZ 001",
        sofor_adi="Test Sofor",
        depo_kapi="A1",
        yukleme_tarihi=date(2026, 3, 31),
        durum=durum,
        notlar="",
        olusturma_tarihi=datetime(2026, 3, 30),
        guncelleme_tarihi=datetime(2026, 3, 30),
    )


class TestSevkiyatPlaniGuncelleUseCase:

    def test_meta_alan_degisimi_basarili(self, sevkiyat_guncelle_uc_mock):
        use_case, mocks = sevkiyat_guncelle_uc_mock
        plan = _make_sevkiyat_entity()
        dto = SevkiyatPlaniGuncelleRequestDTO(tir_plaka="34 DEF 456")

        mocks["sevkiyat_repo"].getir_id_ile.return_value = plan
        mocks["sevkiyat_repo"].guncelle.return_value = _make_sevkiyat_entity()

        result = use_case.execute(plan_id=55, dto=dto, kullanici_id=3)

        assert result.id == 55
        mocks["sevkiyat_repo"].guncelle.assert_called_once()


class TestYuklemeOnaylaUseCase:

    def test_basarili_onayda_tek_commit(self, yukleme_onayla_uc_mock):
        use_case, mocks = yukleme_onayla_uc_mock

        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _make_sevkiyat_entity()
        mocks["sevkiyat_repo"].guncelle.return_value = _make_sevkiyat_entity(
            durum=SevkiyatDurum.YUKLENIYOR
        )
        mocks["siparis_repo"].getir_id_ile.return_value = _make_siparis_entity()

        use_case.execute(plan_id=55, kullanici_id=3)

        assert mocks["sevkiyat_repo"].guncelle.call_args.kwargs["auto_commit"] is False
        mocks["stok_cikis_service"].siparis_bazli_stok_cikisi.assert_called_once()
        mocks["db"].commit.assert_called_once()
        mocks["db"].rollback.assert_not_called()

    def test_stok_cikisi_hatasinda_rollback(self, yukleme_onayla_uc_mock):
        use_case, mocks = yukleme_onayla_uc_mock

        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _make_sevkiyat_entity()
        mocks["sevkiyat_repo"].guncelle.return_value = _make_sevkiyat_entity(
            durum=SevkiyatDurum.YUKLENIYOR
        )
        mocks["siparis_repo"].getir_id_ile.return_value = _make_siparis_entity()
        mocks["stok_cikis_service"].siparis_bazli_stok_cikisi.side_effect = (
            StokVeriUyumsuzluguError("Urun ID: 10")
        )

        with pytest.raises(StokVeriUyumsuzluguError):
            use_case.execute(plan_id=55, kullanici_id=3)

        mocks["db"].rollback.assert_called_once()
        mocks["db"].commit.assert_not_called()

    def test_integrity_hatasinda_rollback_ve_anlamli_hata(self, yukleme_onayla_uc_mock):
        use_case, mocks = yukleme_onayla_uc_mock

        mocks["sevkiyat_repo"].getir_id_ile_kilitli.return_value = _make_sevkiyat_entity()
        mocks["siparis_repo"].getir_id_ile.return_value = _make_siparis_entity()
        mocks["sevkiyat_repo"].guncelle.side_effect = IntegrityError("INSERT", {}, None)

        with pytest.raises(GecersizIslemError, match="aynı anda işlendi"):
            use_case.execute(plan_id=55, kullanici_id=3)

        mocks["db"].rollback.assert_called_once()
        mocks["db"].commit.assert_not_called()
