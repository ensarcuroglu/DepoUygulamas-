"""
Unit testler: Irsaliye ve sevkiyat transaction atomikligi.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.irsaliye_dto import IrsaliyeOlusturRequestDTO
from app.application.dto.sevkiyat_plani_dto import SevkiyatPlaniGuncelleRequestDTO
from app.core.entities.sevkiyat_plani import SevkiyatPlani, SevkiyatDurum
from app.core.exceptions import StokVeriUyumsuzluguError

pytestmark = pytest.mark.unit


def _make_siparis_entity():
    siparis = MagicMock()
    siparis.id = 1
    siparis.siparis_no = "SIP-2026-0001"
    siparis.kalemler = [MagicMock(urun_id=10, miktar=5)]
    return siparis


def _make_irsaliye_entity():
    entity = MagicMock()
    entity.id = 100
    entity.siparis_id = 1
    entity.sevkiyat_id = None
    entity.irsaliye_no = "IRS-2026-0001"
    entity.irsaliye_tarihi = date(2026, 3, 30)
    entity.belge_turu = "SevkIrsaliyesi"
    entity.tir_plaka = "34 ABC 123"
    entity.sofor_adi = "Test Sofor"
    entity.durum = "Taslak"
    entity.olusturma_tarihi = datetime(2026, 3, 30)
    entity.guncelleme_tarihi = datetime(2026, 3, 30)
    return entity


def _make_sevkiyat_entity(durum=SevkiyatDurum.PLANLANDI):
    return SevkiyatPlani(
        id=55,
        siparis_id=1,
        tir_plaka="34 XYZ 001",
        sofor_adi="Test Sofor",
        sofor_telefon="05550000000",
        depo_kapi="A1",
        yukleme_tarihi=date(2026, 3, 31),
        cikis_saati="08:00",
        varis_saati="12:00",
        durum=durum,
        notlar="",
        olusturma_tarihi=datetime(2026, 3, 30),
        guncelleme_tarihi=datetime(2026, 3, 30),
    )


class TestIrsaliyeOlusturUseCase:

    def test_basarili_akista_write_repo_auto_commit_false_ve_tek_commit(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1,
            irsaliye_tarihi=date(2026, 3, 30),
            tir_plaka="34 ABC 123",
            sofor_adi="Test Sofor",
        )

        siparis = _make_siparis_entity()
        mocks["siparis_repo"].getir_id_ile.return_value = siparis
        mocks["sevkiyat_repo"].getir_siparis_id_ile.return_value = None
        mocks["irsaliye_repo"].sonraki_irsaliye_no.return_value = "IRS-2026-0001"
        mocks["irsaliye_repo"].olustur.return_value = _make_irsaliye_entity()

        result = use_case.execute(dto, kullanici_id=7)

        assert result.id == 100
        mocks["irsaliye_repo"].olustur.assert_called_once()
        assert mocks["irsaliye_repo"].olustur.call_args.kwargs["auto_commit"] is False
        mocks["db"].commit.assert_called_once()
        mocks["db"].rollback.assert_not_called()

    def test_stok_cikisi_hatasinda_rollback_yapar_ve_exception_yukseltir(self, irsaliye_olustur_uc_mock):
        use_case, mocks = irsaliye_olustur_uc_mock
        dto = IrsaliyeOlusturRequestDTO(
            siparis_id=1,
            irsaliye_tarihi=date(2026, 3, 30),
        )

        mocks["siparis_repo"].getir_id_ile.return_value = _make_siparis_entity()
        mocks["sevkiyat_repo"].getir_siparis_id_ile.return_value = None
        mocks["irsaliye_repo"].sonraki_irsaliye_no.return_value = "IRS-2026-0001"
        mocks["irsaliye_repo"].olustur.return_value = _make_irsaliye_entity()
        mocks["stok_cikis_service"].siparis_bazli_stok_cikisi.side_effect = StokVeriUyumsuzluguError("Urun ID: 10")

        with pytest.raises(StokVeriUyumsuzluguError):
            use_case.execute(dto, kullanici_id=7)

        mocks["db"].rollback.assert_called_once()
        mocks["db"].commit.assert_not_called()


class TestSevkiyatPlaniGuncelleUseCase:

    def test_write_repo_auto_commit_false_ile_gunceller(self, sevkiyat_guncelle_uc_mock):
        use_case, mocks = sevkiyat_guncelle_uc_mock
        plan = _make_sevkiyat_entity()
        dto = SevkiyatPlaniGuncelleRequestDTO(tir_plaka="34 DEF 456")

        mocks["sevkiyat_repo"].getir_id_ile.return_value = plan
        mocks["sevkiyat_repo"].guncelle.return_value = _make_sevkiyat_entity()

        result = use_case.execute(plan_id=55, dto=dto, kullanici_id=3)

        assert result.id == 55
        mocks["sevkiyat_repo"].guncelle.assert_called_once()
        assert mocks["sevkiyat_repo"].guncelle.call_args.kwargs["auto_commit"] is False
        mocks["db"].commit.assert_called_once()

    def test_yukleniyor_gecisinde_stok_cikisi_hatasi_rollback_yapar(self, sevkiyat_guncelle_uc_mock):
        use_case, mocks = sevkiyat_guncelle_uc_mock
        plan = _make_sevkiyat_entity(durum=SevkiyatDurum.PLANLANDI)
        siparis = _make_siparis_entity()
        dto = SevkiyatPlaniGuncelleRequestDTO(durum=SevkiyatDurum.YUKLENIYOR)

        mocks["sevkiyat_repo"].getir_id_ile.return_value = plan
        mocks["sevkiyat_repo"].guncelle.return_value = _make_sevkiyat_entity(durum=SevkiyatDurum.YUKLENIYOR)
        mocks["siparis_repo"].getir_id_ile.return_value = siparis
        mocks["stok_cikis_service"].siparis_bazli_stok_cikisi.side_effect = StokVeriUyumsuzluguError("Urun ID: 10")

        with pytest.raises(StokVeriUyumsuzluguError):
            use_case.execute(plan_id=55, dto=dto, kullanici_id=3)

        mocks["db"].rollback.assert_called_once()
        mocks["db"].commit.assert_not_called()
