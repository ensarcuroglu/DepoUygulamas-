"""Unit testler: app.application.use_cases.palet_use_cases.

Kapsam: listele, getir (id/barkod), sonraki no, oluştur, güncelle, sil.
Happy path + not found + çakışma + pasif palet davranışları.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.application.dto.palet_dto import (
    PaletGuncelleRequestDTO,
    PaletOlusturRequestDTO,
)
from app.application.use_cases.palet_use_cases import (
    PaletBarkodIleGetirUseCase,
    PaletGetirUseCase,
    PaletGuncelleUseCase,
    PaletListeleUseCase,
    PaletOlusturUseCase,
    PaletSilUseCase,
    PaletSonrakiNumaraUseCase,
)
from app.core.entities.palet import Palet
from app.core.exceptions import CakismaHatasi, KayitBulunamadiError

pytestmark = pytest.mark.unit


def _palet(
    *,
    id: int = 1,
    palet_no: str = "P-001",
    lot_id: int = 10,
    raf_id: int = 5,
    koli_adedi: int = 50,
    aktif: bool = True,
) -> Palet:
    return Palet(
        id=id,
        lot_id=lot_id,
        raf_id=raf_id,
        palet_no=palet_no,
        koli_adedi=koli_adedi,
        aktif=aktif,
        tarih=datetime(2026, 4, 1),
        olusturma_tarihi=datetime(2026, 4, 1),
    )


# ─────────────────────────────────────────────────────────────────
# LİSTELE
# ─────────────────────────────────────────────────────────────────

class TestListele:
    def test_filtreli_arama_delege_edilir(self):
        repo = MagicMock()
        repo.getir_hepsi.return_value = [_palet(id=1), _palet(id=2)]
        uc = PaletListeleUseCase(repo)

        sonuc = uc.execute(skip=0, limit=5, lot_id=10, raf_id=5, ean="123")

        assert len(sonuc) == 2
        repo.getir_hepsi.assert_called_once_with(
            skip=0, limit=5, lot_id=10, raf_id=5, ean="123",
        )


# ─────────────────────────────────────────────────────────────────
# GETİR
# ─────────────────────────────────────────────────────────────────

class TestGetir:
    def test_id_yoksa_hata(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            PaletGetirUseCase(repo).execute(palet_id=1)

    def test_id_varsa_dto(self):
        repo = MagicMock()
        repo.getir_id_ile.return_value = _palet(id=1)
        assert PaletGetirUseCase(repo).execute(palet_id=1).id == 1

    def test_barkod_yoksa_hata(self):
        repo = MagicMock()
        repo.getir_palet_no_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            PaletBarkodIleGetirUseCase(repo).execute(palet_no="P-X")

    def test_barkod_pasif_default_ile_reddedilir(self):
        repo = MagicMock()
        repo.getir_palet_no_ile.return_value = _palet(aktif=False)
        with pytest.raises(KayitBulunamadiError):
            PaletBarkodIleGetirUseCase(repo).execute(palet_no="P-001")

    def test_barkod_include_pasif_donerse_pasif_palet_getirilir(self):
        repo = MagicMock()
        repo.getir_palet_no_ile.return_value = _palet(aktif=False)
        sonuc = PaletBarkodIleGetirUseCase(repo).execute(palet_no="P-001", include_pasif=True)
        assert sonuc.aktif is False


# ─────────────────────────────────────────────────────────────────
# SONRAKİ NO
# ─────────────────────────────────────────────────────────────────

class TestSonrakiNo:
    def test_repo_uretimini_doner(self):
        repo = MagicMock()
        repo.sonraki_palet_no.return_value = "P-2026-0050"
        assert PaletSonrakiNumaraUseCase(repo).execute() == "P-2026-0050"


# ─────────────────────────────────────────────────────────────────
# OLUŞTUR
# ─────────────────────────────────────────────────────────────────

class TestOlustur:
    def _mocks(self):
        return {
            "palet_repo": MagicMock(),
            "lot_repo": MagicMock(),
            "raf_repo": MagicMock(),
            "log_repo": MagicMock(),
        }

    def _dto(self, **over):
        return PaletOlusturRequestDTO(
            lot_id=over.get("lot_id", 10),
            raf_id=over.get("raf_id", 5),
            palet_no=over.get("palet_no", "P-NEW"),
            koli_adedi=over.get("koli_adedi", 50),
            palet_kg=over.get("palet_kg"),
            vardiya=over.get("vardiya"),
        )

    def test_lot_yoksa_hata(self):
        m = self._mocks()
        m["lot_repo"].getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            PaletOlusturUseCase(**m).execute(self._dto(), kullanici_id=5)

    def test_raf_yoksa_hata(self):
        m = self._mocks()
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(id=10)
        m["raf_repo"].getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            PaletOlusturUseCase(**m).execute(self._dto(), kullanici_id=5)

    def test_cakisan_palet_no_reddedilir(self):
        m = self._mocks()
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(id=10)
        m["raf_repo"].getir_id_ile.return_value = SimpleNamespace(id=5)
        m["palet_repo"].getir_palet_no_ile.return_value = _palet(palet_no="P-NEW")
        with pytest.raises(CakismaHatasi):
            PaletOlusturUseCase(**m).execute(self._dto(), kullanici_id=5)
        m["palet_repo"].olustur.assert_not_called()

    def test_happy_path_log_atar(self):
        m = self._mocks()
        m["lot_repo"].getir_id_ile.return_value = SimpleNamespace(id=10)
        m["raf_repo"].getir_id_ile.return_value = SimpleNamespace(id=5)
        m["palet_repo"].getir_palet_no_ile.return_value = None
        m["palet_repo"].olustur.side_effect = lambda p: (setattr(p, "id", 42) or p)

        sonuc = PaletOlusturUseCase(**m).execute(
            self._dto(palet_kg=120.5, vardiya="A"), kullanici_id=5,
        )

        assert sonuc.id == 42
        assert sonuc.palet_kg == 120.5
        assert sonuc.vardiya == "A"
        m["log_repo"].olustur.assert_called_once()


# ─────────────────────────────────────────────────────────────────
# GÜNCELLE
# ─────────────────────────────────────────────────────────────────

class TestGuncelle:
    def test_yoksa_hata(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            PaletGuncelleUseCase(repo, log).execute(1, PaletGuncelleRequestDTO(), kullanici_id=5)

    def test_kismi_guncelleme_exclude_unset(self):
        repo = MagicMock(); log = MagicMock()
        mevcut = _palet(koli_adedi=50)
        repo.getir_id_ile.return_value = mevcut
        repo.guncelle.return_value = mevcut

        dto = PaletGuncelleRequestDTO(koli_adedi=75)
        sonuc = PaletGuncelleUseCase(repo, log).execute(1, dto, kullanici_id=5)

        assert mevcut.koli_adedi == 75
        assert mevcut.aktif is True  # değişmedi
        assert sonuc.koli_adedi == 75
        log.olustur.assert_called_once()

    def test_aktif_false_deaktive_eder(self):
        repo = MagicMock(); log = MagicMock()
        mevcut = _palet(aktif=True)
        repo.getir_id_ile.return_value = mevcut
        repo.guncelle.return_value = mevcut

        PaletGuncelleUseCase(repo, log).execute(1, PaletGuncelleRequestDTO(aktif=False), kullanici_id=5)
        assert mevcut.aktif is False


# ─────────────────────────────────────────────────────────────────
# SİL
# ─────────────────────────────────────────────────────────────────

class TestSil:
    def test_yoksa_hata(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = None
        with pytest.raises(KayitBulunamadiError):
            PaletSilUseCase(repo, log).execute(palet_id=1, kullanici_id=5)

    def test_happy_path_repo_sil_ve_log(self):
        repo = MagicMock(); log = MagicMock()
        repo.getir_id_ile.return_value = _palet(id=1, palet_no="P-001")

        PaletSilUseCase(repo, log).execute(palet_id=1, kullanici_id=5)

        repo.sil.assert_called_once_with(1)
        log.olustur.assert_called_once()
