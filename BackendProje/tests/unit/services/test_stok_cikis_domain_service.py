"""
Unit testler: StokCikisDomainService palet-bazlı hareket üretimi + kritik hata yayılımı.
"""

import pytest
from unittest.mock import MagicMock

from app.core.entities.palet import Palet
from app.core.entities.stok_hareketi import HareketTipi
from app.core.exceptions import StokVeriUyumsuzluguError

pytestmark = pytest.mark.unit


def _make_kalem(urun_id: int, miktar: int):
    kalem = MagicMock()
    kalem.urun_id = urun_id
    kalem.miktar = miktar
    return kalem


def _make_palet(palet_id: int, lot_id: int, raf_id: int, koli_adedi: int) -> Palet:
    return Palet(
        id=palet_id,
        lot_id=lot_id,
        raf_id=raf_id,
        palet_no=f"PLT-{palet_id}",
        koli_adedi=koli_adedi,
    )


class TestSiparisBazliStokCikisi:

    def test_stok_yetersizliginde_loglar_ve_exception_yeniden_firlatir(self, stok_cikis_service_mock):
        service, mocks = stok_cikis_service_mock
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


class TestPaletBazliHareketUretimi:
    """Faz 5: Her palet tüketimi ayrı StokHareketi kaydı üretir (lot_id/palet_id/raf_id dolu)."""

    def test_tek_paletten_tek_hareket_uretir(self, stok_cikis_service_mock):
        service, mocks = stok_cikis_service_mock
        palet = _make_palet(palet_id=11, lot_id=21, raf_id=31, koli_adedi=50)
        mocks["palet_repo"].getir_fifo_sirayla_kilitli.return_value = [palet]

        service.siparis_bazli_stok_cikisi(
            kalemler=[_make_kalem(1, 10)],
            siparis_no="SIP-2026-0002",
            kullanici_id=7,
        )

        assert mocks["hareket_repo"].olustur.call_count == 1
        hareket = mocks["hareket_repo"].olustur.call_args.args[0]
        assert hareket.urun_id == 1
        assert hareket.lot_id == 21
        assert hareket.palet_id == 11
        assert hareket.raf_id == 31
        assert hareket.miktar == 10
        assert hareket.hareket_tipi == HareketTipi.CIKIS
        assert hareket.siparis_no == "SIP-2026-0002"
        assert hareket.irsaliye_no is None

    def test_birden_fazla_palet_tuketilirse_her_palet_icin_ayri_hareket(self, stok_cikis_service_mock):
        service, mocks = stok_cikis_service_mock
        paletler = [
            _make_palet(palet_id=101, lot_id=201, raf_id=301, koli_adedi=6),
            _make_palet(palet_id=102, lot_id=202, raf_id=302, koli_adedi=10),
        ]
        mocks["palet_repo"].getir_fifo_sirayla_kilitli.return_value = paletler

        service.siparis_bazli_stok_cikisi(
            kalemler=[_make_kalem(1, 9)],
            siparis_no="SIP-2026-0003",
            kullanici_id=7,
        )

        assert mocks["hareket_repo"].olustur.call_count == 2
        hareket_1 = mocks["hareket_repo"].olustur.call_args_list[0].args[0]
        hareket_2 = mocks["hareket_repo"].olustur.call_args_list[1].args[0]

        assert (hareket_1.palet_id, hareket_1.lot_id, hareket_1.raf_id, hareket_1.miktar) == (101, 201, 301, 6)
        assert (hareket_2.palet_id, hareket_2.lot_id, hareket_2.raf_id, hareket_2.miktar) == (102, 202, 302, 3)
        assert hareket_1.miktar + hareket_2.miktar == 9

    def test_irsaliye_no_baslangicta_none_birakilir(self, stok_cikis_service_mock):
        service, mocks = stok_cikis_service_mock
        palet = _make_palet(palet_id=1, lot_id=1, raf_id=1, koli_adedi=5)
        mocks["palet_repo"].getir_fifo_sirayla_kilitli.return_value = [palet]

        service.siparis_bazli_stok_cikisi(
            kalemler=[_make_kalem(1, 3)],
            siparis_no="SIP-X",
            kullanici_id=7,
        )

        hareket = mocks["hareket_repo"].olustur.call_args.args[0]
        assert hareket.irsaliye_no is None

    def test_bos_palet_atlanir_hareket_yazilmaz(self, stok_cikis_service_mock):
        service, mocks = stok_cikis_service_mock
        bos_palet = _make_palet(palet_id=50, lot_id=60, raf_id=70, koli_adedi=0)
        dolu_palet = _make_palet(palet_id=51, lot_id=61, raf_id=71, koli_adedi=10)
        mocks["palet_repo"].getir_fifo_sirayla_kilitli.return_value = [bos_palet, dolu_palet]

        service.siparis_bazli_stok_cikisi(
            kalemler=[_make_kalem(1, 5)],
            siparis_no="SIP-X",
            kullanici_id=7,
        )

        # Tek hareket; palet_id=51 (dolu palet).
        assert mocks["hareket_repo"].olustur.call_count == 1
        hareket = mocks["hareket_repo"].olustur.call_args.args[0]
        assert hareket.palet_id == 51
        assert hareket.miktar == 5
