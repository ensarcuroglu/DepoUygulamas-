"""
Unit test fixture'ları — use case katmanı.

Her fixture (use_case, mocks_dict) çifti döndürür:

    use_case, mocks = irsaliye_olustur_uc_mock
"""

import pytest
from unittest.mock import MagicMock

from app.application.use_cases.irsaliye_use_cases import IrsaliyeOlusturUseCase, IrsaliyeGuncelleUseCase
from app.application.use_cases.sevkiyat_plani_use_cases import (
    SevkiyatPlaniGuncelleUseCase,
    SevkiyatPlaniOlusturUseCase,
    SevkiyatPlaniSilUseCase,
    YuklemeOnaylaUseCase,
)
from app.application.use_cases.siparis_use_cases import SiparisGuncelleUseCase


@pytest.fixture
def irsaliye_olustur_uc_mock():
    """IrsaliyeOlusturUseCase ile mock bağımlılık seti."""
    mocks = {
        "irsaliye_repo": MagicMock(),
        "siparis_repo":  MagicMock(),
        "sevkiyat_repo": MagicMock(),
        "log_repo":      MagicMock(),
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
def sevkiyat_olustur_uc_mock():
    """SevkiyatPlaniOlusturUseCase ile mock bağımlılık seti."""
    mocks = {
        "sevkiyat_repo":      MagicMock(),
        "siparis_repo":       MagicMock(),
        "log_repo":           MagicMock(),
        "durum_orchestrator": MagicMock(),
    }
    return SevkiyatPlaniOlusturUseCase(**mocks), mocks


@pytest.fixture
def sevkiyat_guncelle_uc_mock():
    """SevkiyatPlaniGuncelleUseCase ile mock bağımlılık seti."""
    mocks = {
        "sevkiyat_repo":      MagicMock(),
        "log_repo":           MagicMock(),
        "durum_orchestrator": MagicMock(),
    }
    return SevkiyatPlaniGuncelleUseCase(**mocks), mocks


@pytest.fixture
def sevkiyat_sil_uc_mock():
    """SevkiyatPlaniSilUseCase ile mock bağımlılık seti."""
    mocks = {
        "sevkiyat_repo":      MagicMock(),
        "log_repo":           MagicMock(),
        "durum_orchestrator": MagicMock(),
    }
    return SevkiyatPlaniSilUseCase(**mocks), mocks


@pytest.fixture
def yukleme_onayla_uc_mock():
    """YuklemeOnaylaUseCase ile mock bağımlılık seti."""
    mocks = {
        "sevkiyat_repo":      MagicMock(),
        "siparis_repo":       MagicMock(),
        "hareket_repo":       MagicMock(),
        "log_repo":           MagicMock(),
        "stok_cikis_service": MagicMock(),
        "db":                 MagicMock(),
        "durum_orchestrator": MagicMock(),
    }
    mocks["hareket_repo"].siparis_icin_cikis_var_mi.return_value = False
    return YuklemeOnaylaUseCase(**mocks), mocks


@pytest.fixture
def siparis_guncelle_uc_mock():
    """SiparisGuncelleUseCase ile mock bağımlılık seti."""
    mocks = {
        "siparis_repo": MagicMock(),
        "log_repo":     MagicMock(),
    }
    return SiparisGuncelleUseCase(**mocks), mocks
