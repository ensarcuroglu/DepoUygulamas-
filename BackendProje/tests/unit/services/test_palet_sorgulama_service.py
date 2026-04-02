"""
Unit testler: PaletSorgulamaService — DB vs veri kaynagi fallback (mock repo ile).
"""

import pytest

from app.core.entities.palet import Palet
from app.core.entities.lot import Lot
from app.core.entities.raf import Raf
from app.application.dto.palet_bilgi_dto import PaletBilgiDTO
from unittest.mock import MagicMock

pytestmark = pytest.mark.unit


def _make_urun_mock(isim="Test Urun", barkod="1234567890123"):
    urun = MagicMock()
    urun.isim = isim
    urun.barkod = barkod
    return urun


def _make_depo_mock(isim="Depo-A"):
    depo = MagicMock()
    depo.isim = isim
    return depo


def _setup_db_palet(m, koli_adedi=80, aktif=True):
    """DB palet sorgulama icin ortak mock setup."""
    palet = Palet(id=10, lot_id=1, raf_id=5, palet_no="PLT-2026-00001", koli_adedi=koli_adedi, aktif=aktif)
    m["palet_repo"].getir_palet_no_ile.return_value = palet
    m["lot_repo"].getir_id_ile.return_value = Lot(id=1, urun_id=1, lot_no="LOT-2026-0001")
    m["urun_repo"].getir_id_ile.return_value = _make_urun_mock()
    m["raf_repo"].getir_id_ile.return_value = Raf(id=5, depo_id=1, kod="R-01-A")
    m["depo_repo"].getir_id_ile.return_value = _make_depo_mock()
    return palet


class TestPaletSorgula:

    def test_db_palet_var_sistem_kaynagi_doner(self, palet_sorgulama_service_mock):
        service, m = palet_sorgulama_service_mock
        _setup_db_palet(m, koli_adedi=80)

        result = service.sorgula("PLT-2026-00001")

        assert isinstance(result, PaletBilgiDTO)
        assert result.kaynak == "sistem"
        assert result.palet_no == "PLT-2026-00001"
        assert result.miktar == 80
        assert result.giris_yapildi_mi is True
        m["veri_kaynagi"].palet_bilgisi_getir.assert_not_called()

    def test_db_palet_yok_veri_kaynasindan_doner(self, palet_sorgulama_service_mock):
        service, m = palet_sorgulama_service_mock
        expected_dto = PaletBilgiDTO(
            palet_no="PLT-2026-00099",
            urun_id=1, urun_adi="Test Urun", miktar=50,
            depo_id=1, depo_adi="Depo-A",
            durum="aktif", kaynak="irsaliye", giris_yapildi_mi=False,
        )

        m["palet_repo"].getir_palet_no_ile.return_value = None
        m["veri_kaynagi"].palet_bilgisi_getir.return_value = expected_dto

        result = service.sorgula("PLT-2026-00099")

        assert result.kaynak == "irsaliye"
        assert result.giris_yapildi_mi is False
        m["veri_kaynagi"].palet_bilgisi_getir.assert_called_once_with("PLT-2026-00099")

    def test_db_palet_pasif_durum_doner(self, palet_sorgulama_service_mock):
        service, m = palet_sorgulama_service_mock
        _setup_db_palet(m, koli_adedi=0, aktif=False)

        result = service.sorgula("PLT-2026-00001")

        assert result.durum == "pasif"
