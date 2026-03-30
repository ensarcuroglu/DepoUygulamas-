"""
Unit testler: StokCikisDomainService kritik hata yayilimi.
"""

import pytest
from unittest.mock import MagicMock

from app.core.exceptions import StokVeriUyumsuzluguError
from app.core.services.stok_cikis_domain_service import StokCikisDomainService

pytestmark = pytest.mark.unit


def _make_service():
    mocks = {
        "palet_repo": MagicMock(),
        "hareket_repo": MagicMock(),
        "log_repo": MagicMock(),
    }
    return StokCikisDomainService(**mocks), mocks


def _make_kalem(urun_id: int, miktar: int):
    kalem = MagicMock()
    kalem.urun_id = urun_id
    kalem.miktar = miktar
    return kalem


class TestSiparisBazliStokCikisi:

    def test_stok_yetersizliginde_loglar_ve_exception_yeniden_firlatir(self):
        service, mocks = _make_service()
        kalemler = [_make_kalem(1, 10), _make_kalem(2, 5)]

        mocks["palet_repo"].getir_fifo_sirayla_kilitli.return_value = []

        with pytest.raises(StokVeriUyumsuzluguError):
            service.siparis_bazli_stok_cikisi(
                kalemler=kalemler,
                siparis_no="SIP-2026-0001",
                kullanici_id=99,
            )

        mocks["log_repo"].olustur.assert_called_once()
        mocks["hareket_repo"].olustur.assert_not_called()
        mocks["palet_repo"].getir_fifo_sirayla_kilitli.assert_called_once_with(1)
