from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.application.dto.toplama_gorevi_dto import FefoOverrideRequestDTO
from app.application.use_cases.toplama_gorevi_use_cases import (
    FefoOverrideUseCase,
    GorevTamamlaUseCase,
)
from app.core.entities.toplama_gorevi import ToplamaGorevi, ToplamaGoreviDurum
from app.core.exceptions import GecersizIslemError, YetkisizIslemError

pytestmark = pytest.mark.unit


def _gorev(
    *,
    durum=ToplamaGoreviDurum.DEVAM_EDIYOR,
    atanan_kullanici_id=10,
    urun_id=501,
    palet_id=1001,
    lot_id=2001,
):
    return ToplamaGorevi(
        id=1,
        sevkiyat_id=55,
        palet_id=palet_id,
        lot_id=lot_id,
        urun_id=urun_id,
        depo_id=7,
        atanan_kullanici_id=atanan_kullanici_id,
        durum=durum,
        sira_no=1,
        olusturma_tarihi=datetime(2026, 4, 15, 12, 0, 0),
    )


class TestGorevTamamlaGuvenlik:

    def test_yalnizca_atanan_operator_tamamlayabilir(self):
        gorev_repo = MagicMock()
        gorev_repo.getir_id_ile.return_value = _gorev(atanan_kullanici_id=10)
        uc = GorevTamamlaUseCase(
            gorev_repo=gorev_repo,
            palet_repo=MagicMock(),
            rezervasyon_repo=MagicMock(),
            hareket_repo=MagicMock(),
            log_repo=MagicMock(),
        )

        with pytest.raises(YetkisizIslemError, match="atanan"):
            uc.execute(gorev_id=1, kullanici_id=11)

        gorev_repo.guncelle.assert_not_called()


class TestFefoOverrideGuvenlik:

    def test_farkli_urune_ait_palet_reddedilir(self):
        gorev_repo = MagicMock()
        gorev_repo.getir_id_ile.return_value = _gorev(
            durum=ToplamaGoreviDurum.BEKLEMEDE,
            urun_id=501,
            palet_id=1001,
        )

        yeni_palet = MagicMock()
        yeni_palet.aktif = True
        yeni_palet.lot = MagicMock(urun_id=999)
        yeni_palet.lot_id = 3001

        rezervasyon_repo = MagicMock()
        uc = FefoOverrideUseCase(
            gorev_repo=gorev_repo,
            rezervasyon_repo=rezervasyon_repo,
            palet_repo=MagicMock(getir_id_ile=MagicMock(return_value=yeni_palet)),
            log_repo=MagicMock(),
        )

        dto = FefoOverrideRequestDTO(
            yeni_palet_id=2002,
            override_neden="Operasyonel zorunluluk nedeniyle degistir.",
        )

        with pytest.raises(GecersizIslemError, match="aktif paletler"):
            uc.execute(gorev_id=1, dto=dto, kullanici_id=3, kullanici_rol="admin")

        rezervasyon_repo.getir_aktif_by_palet.assert_not_called()
        gorev_repo.guncelle.assert_not_called()

    def test_aktif_rezervasyonlu_palet_reddedilir(self):
        gorev_repo = MagicMock()
        gorev_repo.getir_id_ile.return_value = _gorev(
            durum=ToplamaGoreviDurum.BEKLEMEDE,
            urun_id=501,
            palet_id=1001,
        )

        yeni_palet = MagicMock()
        yeni_palet.aktif = True
        yeni_palet.lot = MagicMock(urun_id=501)
        yeni_palet.lot_id = 3001

        rezervasyon_repo = MagicMock()
        rezervasyon_repo.getir_aktif_by_palet.return_value = MagicMock()
        uc = FefoOverrideUseCase(
            gorev_repo=gorev_repo,
            rezervasyon_repo=rezervasyon_repo,
            palet_repo=MagicMock(getir_id_ile=MagicMock(return_value=yeni_palet)),
            log_repo=MagicMock(),
        )

        dto = FefoOverrideRequestDTO(
            yeni_palet_id=2002,
            override_neden="Acil saha dengesizligi nedeniyle degistir.",
        )

        with pytest.raises(GecersizIslemError, match="zaten"):
            uc.execute(gorev_id=1, dto=dto, kullanici_id=3, kullanici_rol="admin")

        gorev_repo.guncelle.assert_not_called()
