"""
Unit testler: TopluPaletCikisRequestDTO alan uzunlugu validasyonlari.
"""

import pytest
from pydantic import ValidationError

from app.application.dto.stok_islemleri_dto import TopluPaletCikisRequestDTO

pytestmark = pytest.mark.unit


def _gecerli_payload(**overrides):
    base = {
        "kalemler": [{"palet_no": "PLT-2026-00001", "miktar": 5}],
        "siparis_no": "SIP-2026-0001",
        "tir_plaka": "34 ABC 123",
        "depo_kapi": "Kapi-1",
        "sofor_adi": "Test Sofor",
        "tasiyici_firma": "Test Lojistik",
        "aciklama": "Test cikis islemi",
    }
    base.update(overrides)
    return base


def test_tir_plaka_max_uzunluk_asimi():
    with pytest.raises(ValidationError):
        TopluPaletCikisRequestDTO(**_gecerli_payload(tir_plaka="x" * 51))


def test_depo_kapi_max_uzunluk_asimi():
    with pytest.raises(ValidationError):
        TopluPaletCikisRequestDTO(**_gecerli_payload(depo_kapi="x" * 51))


def test_sofor_adi_max_uzunluk_asimi():
    with pytest.raises(ValidationError):
        TopluPaletCikisRequestDTO(**_gecerli_payload(sofor_adi="x" * 101))


def test_tasiyici_firma_max_uzunluk_asimi():
    with pytest.raises(ValidationError):
        TopluPaletCikisRequestDTO(**_gecerli_payload(tasiyici_firma="x" * 101))
