
from app.core.entities.palet import Palet
from app.core.entities.kullanici import Kullanici
from unittest.mock import MagicMock


def test_palet_cikis_kilitli_okuma_yapar(palet_stok_service_mock):
    service, m = palet_stok_service_mock

    palet = Palet(id=1, palet_no="PLT-TEST-001", koli_adedi=10, aktif=True, lot_id=1)
    kullanici = Kullanici(id=1)
    kullanici.depo_erisim_var = MagicMock(return_value=True)

    m["palet_repo"].getir_palet_no_ile.return_value = palet
    m["raf_repo"].getir_id_ile.return_value = None

    service.palet_cikis(palet_no="PLT-TEST-001", kullanici=kullanici, miktar=5)

    m["palet_repo"].getir_palet_no_ile.assert_called_once_with("PLT-TEST-001", kilitli_mi=True)
