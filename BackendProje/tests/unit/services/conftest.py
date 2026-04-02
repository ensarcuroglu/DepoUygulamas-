"""
Unit test fixture'ları — servis katmanı.

Her fixture (service, mocks_dict) çifti döndürür; bu sayede mevcut
_make_service() çağrılarının yerini birebir alabilir:

    service, m = palet_stok_service_mock
"""

import pytest
from unittest.mock import MagicMock

from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService
from app.core.services.stok_cikis_domain_service import StokCikisDomainService
from app.infrastructure.services.palet_sorgulama_service import PaletSorgulamaService


@pytest.fixture
def palet_stok_service_mock():
    """PaletBazliStokDomainService ile tam mock repo seti."""
    mocks = {
        "veri_kaynagi": MagicMock(),
        "palet_repo":   MagicMock(),
        "lot_repo":     MagicMock(),
        "raf_repo":     MagicMock(),
        "hareket_repo": MagicMock(),
        "log_repo":     MagicMock(),
    }
    return PaletBazliStokDomainService(**mocks), mocks


@pytest.fixture
def stok_cikis_service_mock():
    """StokCikisDomainService ile mock repo seti."""
    mocks = {
        "palet_repo":   MagicMock(),
        "hareket_repo": MagicMock(),
        "log_repo":     MagicMock(),
    }
    return StokCikisDomainService(**mocks), mocks


@pytest.fixture
def palet_sorgulama_service_mock():
    """PaletSorgulamaService ile mock repo seti."""
    mocks = {
        "veri_kaynagi": MagicMock(),
        "palet_repo":   MagicMock(),
        "lot_repo":     MagicMock(),
        "urun_repo":    MagicMock(),
        "depo_repo":    MagicMock(),
        "raf_repo":     MagicMock(),
    }
    return PaletSorgulamaService(**mocks), mocks
