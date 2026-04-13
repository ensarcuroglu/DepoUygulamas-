"""
Unit test fixture'ları — use case katmanı.

Her fixture (use_case, mocks_dict) çifti döndürür:

    use_case, mocks = irsaliye_olustur_uc_mock
"""

import pytest
from unittest.mock import MagicMock

from app.application.use_cases.irsaliye_use_cases import IrsaliyeOlusturUseCase, IrsaliyeGuncelleUseCase
from app.application.use_cases.sevkiyat_plani_use_cases import SevkiyatPlaniGuncelleUseCase


@pytest.fixture
def irsaliye_olustur_uc_mock():
    """IrsaliyeOlusturUseCase ile mock bağımlılık seti."""
    mocks = {
        "irsaliye_repo":      MagicMock(),
        "siparis_repo":       MagicMock(),
        "sevkiyat_repo":      MagicMock(),
        "hareket_repo":       MagicMock(),
        "log_repo":           MagicMock(),
        "stok_cikis_service": MagicMock(),
        "db":                 MagicMock(),
    }
    return IrsaliyeOlusturUseCase(**mocks), mocks


@pytest.fixture
def irsaliye_guncelle_uc_mock():
    """IrsaliyeGuncelleUseCase ile mock bağımlılık seti."""
    mocks = {
        "irsaliye_repo": MagicMock(),
        "log_repo":      MagicMock(),
    }
    return IrsaliyeGuncelleUseCase(**mocks), mocks


@pytest.fixture
def sevkiyat_guncelle_uc_mock():
    """SevkiyatPlaniGuncelleUseCase ile mock bağımlılık seti."""
    mocks = {
        "sevkiyat_repo":      MagicMock(),
        "siparis_repo":       MagicMock(),
        "log_repo":           MagicMock(),
        "stok_cikis_service": MagicMock(),
        "db":                 MagicMock(),
    }
    return SevkiyatPlaniGuncelleUseCase(**mocks), mocks
