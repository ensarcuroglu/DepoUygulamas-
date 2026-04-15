"""
Faz 5 testleri — İzlenebilirlik (irsaliye_no backfill).

Kapsam:
- İrsaliye KESILDI geçişinde açık çıkış hareketleri irsaliye_no ile güncellenir.
- İrsaliye GONDERILDI geçişinde aynı backfill tetiklenir.
- Durum değişmediğinde backfill tetiklenmez.
- Evrak alanlarının güncellenmesi (durum değişmezse) backfill tetiklemez.
"""

from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.irsaliye_dto import IrsaliyeGuncelleRequestDTO
from app.core.entities.irsaliye import IrsaliyeDurum

pytestmark = pytest.mark.unit


def _irsaliye(durum=IrsaliyeDurum.TASLAK, irsaliye_no="IRS-2026-0050"):
    entity = MagicMock()
    entity.id = 200
    entity.siparis_id = 1
    entity.sevkiyat_id = 55
    entity.irsaliye_no = irsaliye_no
    entity.irsaliye_tarihi = date(2026, 4, 14)
    entity.belge_turu = "SevkIrsaliyesi"
    entity.tir_plaka = None
    entity.sofor_adi = None
    entity.durum = durum
    entity.olusturma_tarihi = datetime(2026, 4, 14)
    entity.guncelleme_tarihi = datetime(2026, 4, 14)
    entity.duzenlenebilir_mi = MagicMock(return_value=(durum == IrsaliyeDurum.TASLAK))
    return entity


def _siparis(siparis_no="SIP-2026-0001"):
    siparis = MagicMock()
    siparis.id = 1
    siparis.siparis_no = siparis_no
    return siparis


class TestIrsaliyeKesildiBackfill:

    def test_kesildi_gecisi_backfill_tetikler(self, irsaliye_guncelle_uc_mock):
        uc, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _irsaliye(durum=IrsaliyeDurum.TASLAK, irsaliye_no="IRS-2026-0050")
        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye
        mocks["irsaliye_repo"].guncelle.return_value = irsaliye
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis("SIP-2026-0001")

        dto = IrsaliyeGuncelleRequestDTO(durum=IrsaliyeDurum.KESILDI)
        uc.execute(irsaliye_id=200, dto=dto, kullanici_id=7)

        mocks["hareket_repo"].siparis_icin_irsaliye_no_guncelle.assert_called_once_with(
            "SIP-2026-0001", "IRS-2026-0050", auto_commit=False,
        )

    def test_gonderildi_gecisi_backfill_tetikler(self, irsaliye_guncelle_uc_mock):
        uc, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _irsaliye(durum=IrsaliyeDurum.KESILDI, irsaliye_no="IRS-2026-0050")
        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye
        mocks["irsaliye_repo"].guncelle.return_value = irsaliye
        mocks["siparis_repo"].getir_id_ile.return_value = _siparis("SIP-2026-0001")

        dto = IrsaliyeGuncelleRequestDTO(durum=IrsaliyeDurum.GONDERILDI)
        uc.execute(irsaliye_id=200, dto=dto, kullanici_id=7)

        mocks["hareket_repo"].siparis_icin_irsaliye_no_guncelle.assert_called_once()

    def test_durum_degismediyse_backfill_tetiklenmez(self, irsaliye_guncelle_uc_mock):
        uc, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _irsaliye(durum=IrsaliyeDurum.TASLAK)
        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye
        mocks["irsaliye_repo"].guncelle.return_value = irsaliye

        dto = IrsaliyeGuncelleRequestDTO(tir_plaka="34 ABC 12")
        uc.execute(irsaliye_id=200, dto=dto, kullanici_id=7)

        mocks["hareket_repo"].siparis_icin_irsaliye_no_guncelle.assert_not_called()

    def test_siparis_bulunamazsa_backfill_atlanir(self, irsaliye_guncelle_uc_mock):
        uc, mocks = irsaliye_guncelle_uc_mock
        irsaliye = _irsaliye(durum=IrsaliyeDurum.TASLAK)
        mocks["irsaliye_repo"].getir_id_ile.return_value = irsaliye
        mocks["irsaliye_repo"].guncelle.return_value = irsaliye
        mocks["siparis_repo"].getir_id_ile.return_value = None

        dto = IrsaliyeGuncelleRequestDTO(durum=IrsaliyeDurum.KESILDI)
        uc.execute(irsaliye_id=200, dto=dto, kullanici_id=7)

        mocks["hareket_repo"].siparis_icin_irsaliye_no_guncelle.assert_not_called()
