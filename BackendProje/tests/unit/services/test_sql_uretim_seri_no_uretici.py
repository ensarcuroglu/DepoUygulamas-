"""Unit testleri — SqlUretimSeriNoUretici.

TC-001: Birden fazla çağrı benzersiz ve formatında seri numara üretir.
Concurrency testi sayaç mock'u ile kontrol edilir; gerçek DB kiliti
integration testlerde doğrulanmalıdır.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock

from app.infrastructure.services.sql_uretim_seri_no_uretici import SqlUretimSeriNoUretici


@pytest.fixture
def sayac_repo():
    return MagicMock()


@pytest.fixture
def uretici(sayac_repo):
    return SqlUretimSeriNoUretici(sayac_repo)


class TestSeriNoUretici:
    def test_format_dogru(self, uretici: SqlUretimSeriNoUretici, sayac_repo):
        sayac_repo.artir_ve_dondur.return_value = 1
        seri = uretici.uret(date(2025, 4, 16))
        assert seri == "PRD-20250416-0001"

    def test_dort_hane_padding(self, uretici: SqlUretimSeriNoUretici, sayac_repo):
        sayac_repo.artir_ve_dondur.return_value = 42
        seri = uretici.uret(date(2025, 4, 16))
        assert seri == "PRD-20250416-0042"

    def test_tc001_10_cagri_unique_seri_no(
        self, uretici: SqlUretimSeriNoUretici, sayac_repo
    ):
        """TC-001: Sıralı 10 çağrı → 10 benzersiz seri no, çakışma yok."""
        tarih = date(2025, 4, 16)
        sayac_repo.artir_ve_dondur.side_effect = list(range(1, 11))

        sonuclar = [uretici.uret(tarih) for _ in range(10)]

        assert len(sonuclar) == 10
        assert len(set(sonuclar)) == 10  # tümü benzersiz
        assert all(s.startswith("PRD-20250416-") for s in sonuclar)
        assert sonuclar[0] == "PRD-20250416-0001"
        assert sonuclar[9] == "PRD-20250416-0010"

    def test_sayac_repo_cagirilir(
        self, uretici: SqlUretimSeriNoUretici, sayac_repo
    ):
        sayac_repo.artir_ve_dondur.return_value = 5
        tarih = date(2025, 4, 16)
        uretici.uret(tarih)
        sayac_repo.artir_ve_dondur.assert_called_once_with(tarih)

    def test_farkli_tarihler_farkli_prefix(
        self, uretici: SqlUretimSeriNoUretici, sayac_repo
    ):
        sayac_repo.artir_ve_dondur.return_value = 1
        assert uretici.uret(date(2025, 1, 1)) == "PRD-20250101-0001"
        assert uretici.uret(date(2025, 12, 31)) == "PRD-20251231-0001"
