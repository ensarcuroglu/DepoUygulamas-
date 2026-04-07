"""
Unit testler: Urun Use Case iş mantığı (mock repository ile)
Clean Architecture katmanındaki use case'leri test eder.
"""

import pytest
from unittest.mock import MagicMock

from app.application.use_cases.urun_use_cases import (
    UrunOlusturUseCase,
    UrunGetirUseCase,
    UrunListeleUseCase,
    UrunSilUseCase,
)
from app.application.dto.urun_dto import UrunOlusturRequestDTO, UrunResponseDTO
from app.core.exceptions import KayitBulunamadiError, CakismaHatasi

pytestmark = pytest.mark.unit


def _mock_urun_entity(**overrides):
    """Test için mock ürün entity'si oluşturur. Alanlar UrunResponseDTO.from_entity ile uyumlu."""
    from datetime import datetime
    defaults = dict(
        id=1, isim="Test Ürün", barkod="1234567890123", ean=None,
        ic_adet=1, gramaj=None, birim="Adet", fiyat=25.0,
        min_stok=5, aciklama="", stok_miktari=0, durum="Stok Yok",
        aktif=True, marka_id=None, kategori_id=None, tedarikci_id=None,
        depolama_tipi="Kuru",
        olusturma_tarihi=datetime(2026, 1, 1),
        guncelleme_tarihi=datetime(2026, 1, 1),
    )
    defaults.update(overrides)
    entity = MagicMock()
    for k, v in defaults.items():
        setattr(entity, k, v)
    return entity


def _make_olustur_use_case():
    """UrunOlusturUseCase için mock repo'lu kurulum."""
    mock_urun_repo = MagicMock()
    mock_log_repo = MagicMock()
    return UrunOlusturUseCase(mock_urun_repo, mock_log_repo), mock_urun_repo, mock_log_repo


def _make_sil_use_case():
    """UrunSilUseCase için mock repo'lu kurulum."""
    mock_urun_repo = MagicMock()
    mock_log_repo = MagicMock()
    return UrunSilUseCase(mock_urun_repo, mock_log_repo), mock_urun_repo, mock_log_repo


class TestUrunOlusturUseCase:
    """UrunOlusturUseCase iş kuralı testleri."""

    def test_basarili_olusturma(self):
        use_case, mock_urun_repo, mock_log_repo = _make_olustur_use_case()

        dto = UrunOlusturRequestDTO(
            isim="Test Ürün",
            barkod="1234567890123",
            birim="Adet",
            fiyat=25.0,
            min_stok=5,
        )

        mock_urun_repo.getir_barkod_ile.return_value = None
        mock_urun_repo.olustur.return_value = _mock_urun_entity()

        result = use_case.execute(dto, kullanici_id=1)

        mock_urun_repo.olustur.assert_called_once()
        mock_log_repo.olustur.assert_called_once()
        assert result.id == 1
        assert result.isim == "Test Ürün"

    def test_barkod_cakismasi(self):
        use_case, mock_urun_repo, _ = _make_olustur_use_case()

        dto = UrunOlusturRequestDTO(
            isim="Çakışan Ürün",
            barkod="1234567890123",
        )

        mock_urun_repo.getir_barkod_ile.return_value = _mock_urun_entity()

        with pytest.raises(CakismaHatasi):
            use_case.execute(dto, kullanici_id=1)

        mock_urun_repo.olustur.assert_not_called()


class TestUrunGetirUseCase:
    """UrunGetirUseCase testleri."""

    def test_basarili_getir(self):
        mock_repo = MagicMock()
        use_case = UrunGetirUseCase(mock_repo)

        mock_repo.getir_id_ile.return_value = _mock_urun_entity(id=5, isim="Bulunan Ürün")

        result = use_case.by_id(5)
        assert result.id == 5
        assert result.isim == "Bulunan Ürün"

    def test_bulunamadi(self):
        mock_repo = MagicMock()
        use_case = UrunGetirUseCase(mock_repo)
        mock_repo.getir_id_ile.return_value = None

        with pytest.raises(KayitBulunamadiError):
            use_case.by_id(999)

    def test_barkod_ile_getir(self):
        mock_repo = MagicMock()
        use_case = UrunGetirUseCase(mock_repo)
        mock_repo.getir_barkod_ile.return_value = _mock_urun_entity(barkod="9999999999999")

        result = use_case.by_barkod("9999999999999")
        assert result.barkod == "9999999999999"


class TestUrunListeleUseCase:
    """UrunListeleUseCase testleri."""

    def test_bos_liste(self):
        mock_repo = MagicMock()
        use_case = UrunListeleUseCase(mock_repo)
        mock_repo.getir_hepsi.return_value = []

        result = use_case.execute()
        assert result == []

    def test_filtreli_listeleme(self):
        mock_repo = MagicMock()
        use_case = UrunListeleUseCase(mock_repo)
        mock_repo.getir_hepsi.return_value = [_mock_urun_entity()]

        result = use_case.execute(search="test", kategori_id=1)

        mock_repo.getir_hepsi.assert_called_once_with(
            skip=0, limit=50, search="test", kategori_id=1, marka_id=None,
        )
        assert len(result) == 1


class TestUrunSilUseCase:
    """UrunSilUseCase testleri."""

    def test_basarili_silme(self):
        use_case, mock_urun_repo, mock_log_repo = _make_sil_use_case()
        mock_urun_repo.getir_id_ile.return_value = _mock_urun_entity(id=1)

        use_case.execute(urun_id=1, kullanici_id=1)

        mock_urun_repo.sil.assert_called_once_with(1)
        mock_log_repo.olustur.assert_called_once()

    def test_olmayan_urun_silme(self):
        use_case, mock_urun_repo, _ = _make_sil_use_case()
        mock_urun_repo.getir_id_ile.return_value = None

        with pytest.raises(KayitBulunamadiError):
            use_case.execute(urun_id=999, kullanici_id=1)
