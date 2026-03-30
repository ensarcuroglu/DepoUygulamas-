import pytest
from unittest.mock import MagicMock

from app.core.entities.palet import Palet
from app.core.entities.kullanici import Kullanici
from app.core.services.palet_bazli_stok_domain_service import PaletBazliStokDomainService

def test_palet_cikis_kilitli_okuma_yapar():
    # 1. Hazırlık (Mock Repository'ler)
    mock_palet_repo = MagicMock()
    mock_log_repo = MagicMock()
    mock_hareket_repo = MagicMock()
    mock_raf_repo = MagicMock()
    mock_lot_repo = MagicMock()
    mock_veri_kaynagi = MagicMock()

    service = PaletBazliStokDomainService(
        veri_kaynagi=mock_veri_kaynagi,
        palet_repo=mock_palet_repo,
        lot_repo=mock_lot_repo,
        raf_repo=mock_raf_repo,
        hareket_repo=mock_hareket_repo,
        log_repo=mock_log_repo
    )

    # Sahte bir palet ve kullanıcı oluştur
    palet = Palet(id=1, palet_no="PLT-TEST-001", koli_adedi=10, aktif=True, lot_id=1)
    kullanici = Kullanici(id=1)
    kullanici.depo_erisim_var = MagicMock(return_value=True) # Depo yetkisi var sayıyoruz

    mock_palet_repo.getir_palet_no_ile.return_value = palet
    mock_raf_repo.getir_id_ile.return_value = None 

    # 2. İşlem: 5 koli çıkış yap
    service.palet_cikis(palet_no="PLT-TEST-001", kullanici=kullanici, miktar=5)

    # 3. Doğrulama: Repository kilitli_mi=True ile çağrılmış olmalı!
    mock_palet_repo.getir_palet_no_ile.assert_called_once_with("PLT-TEST-001", kilitli_mi=True)