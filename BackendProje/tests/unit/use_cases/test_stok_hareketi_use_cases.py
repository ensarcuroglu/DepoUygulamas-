"""
Unit testler: StokHareketiOlusturUseCase.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.application.dto.stok_hareketi_dto import StokHareketiOlusturRequestDTO
from app.application.use_cases.stok_hareketi_use_cases import StokHareketiOlusturUseCase

pytestmark = pytest.mark.unit


def _build_use_case():
    mocks = {
        "urun_repo": MagicMock(),
        "lot_repo": MagicMock(),
        "palet_repo": MagicMock(),
        "hareket_repo": MagicMock(),
        "log_repo": MagicMock(),
        "db": MagicMock(),
    }
    use_case = StokHareketiOlusturUseCase(**mocks)
    return use_case, mocks


def test_execute_cikis_sevkiyat_alanlarini_persist_eder():
    use_case, mocks = _build_use_case()
    mocks["urun_repo"].getir_id_ile.return_value = SimpleNamespace(id=1, isim="Test Urun")

    def _olustur(entity, auto_commit=False):
        entity.id = 123
        return entity

    mocks["hareket_repo"].olustur.side_effect = _olustur

    dto = StokHareketiOlusturRequestDTO(
        urun_id=1,
        hareket_tipi="cikis",
        miktar=10,
        siparis_no="SIP-2026-0001",
        sofor_adi="Ali Veli",
        tasiyici_firma="Demo Lojistik",
    )

    with patch.object(use_case, "_cikis_isle", side_effect=lambda hareket, _urun: hareket):
        result = use_case.execute(dto, kullanici_id=99)

    kaydedilen_hareket = mocks["hareket_repo"].olustur.call_args.args[0]
    assert kaydedilen_hareket.sofor_adi == "Ali Veli"
    assert kaydedilen_hareket.tasiyici_firma == "Demo Lojistik"
    assert result.sofor_adi == "Ali Veli"
    assert result.tasiyici_firma == "Demo Lojistik"
