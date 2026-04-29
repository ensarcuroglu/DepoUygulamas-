"""
Unit testler: RafOneriSorgulaUseCase (akıllı yerleştirme öneri sorgusu).

Kapsam:
- Palet yoksa KayitBulunamadiError
- Palet'in lot/urun bilgisi yoksa GecersizIslemError
- Paletin raf bağlamından depo çözülemezse GecersizIslemError
- Depo filtresi farklıysa YetkisizIslemError
- Algoritma None dönerse uyarı dolu, onerilen None
- Algoritma öneri dönerse DTO doğru zenginleşir (bileşenler + bos_slot)
"""

from __future__ import annotations
from unittest.mock import MagicMock

import pytest

from app.application.use_cases.yerlestirme_gorevi_use_cases import RafOneriSorgulaUseCase
from app.core.entities.palet import Palet
from app.core.entities.raf import Raf
from app.core.entities.urun import Urun
from app.core.entities.zon import Zon, ZonTipi
from app.core.exceptions import (
    KayitBulunamadiError,
    GecersizIslemError,
    YetkisizIslemError,
)
from app.core.services.yerlestirme_algoritmasi import (
    AlternatifOneri,
    YerlestirmeOnerisi,
)

pytestmark = pytest.mark.unit


def _palet(id=1, lot_id=1, raf_id=10) -> Palet:
    return Palet(id=id, lot_id=lot_id, raf_id=raf_id, palet_no=f"PLT-{id:06d}", aktif=True)


def _raf(id=10, depo_id=1, zon_id=1, kapasite=10) -> Raf:
    return Raf(id=id, depo_id=depo_id, zon_id=zon_id, kod=f"RAF-{id:03d}", kapasite=kapasite)


def _urun(id=1) -> Urun:
    return Urun(id=id, isim="Test Ürün", depolama_tipi="Kuru")


def _kur(palet=None, lot=None, urun=None, raf=None, zon=None, oneri=None):
    palet_repo = MagicMock()
    lot_repo = MagicMock()
    urun_repo = MagicMock()
    raf_repo = MagicMock()
    zon_repo = MagicMock()
    algoritma = MagicMock()

    palet_repo.getir_id_ile.return_value = palet
    palet_repo.getir_hepsi.return_value = []
    lot_repo.getir_id_ile.return_value = lot
    urun_repo.getir_id_ile.return_value = urun
    raf_repo.getir_id_ile.return_value = raf
    zon_repo.getir_id_ile.return_value = zon
    algoritma.raf_oner.return_value = oneri

    uc = RafOneriSorgulaUseCase(
        palet_repo=palet_repo,
        lot_repo=lot_repo,
        urun_repo=urun_repo,
        raf_repo=raf_repo,
        zon_repo=zon_repo,
        algoritma=algoritma,
    )
    return uc, palet_repo, lot_repo, urun_repo, raf_repo, zon_repo, algoritma


def test_palet_yoksa_kayit_bulunamadi():
    uc, *_ = _kur(palet=None)
    with pytest.raises(KayitBulunamadiError):
        uc.execute(palet_id=999)


def test_lot_yoksa_gecersiz_islem():
    palet = _palet()
    uc, *_ = _kur(palet=palet, lot=None, raf=_raf())
    with pytest.raises(GecersizIslemError):
        uc.execute(palet_id=palet.id)


def test_urun_yoksa_gecersiz_islem():
    palet = _palet()
    lot = MagicMock(urun_id=42)
    uc, *_ = _kur(palet=palet, lot=lot, urun=None, raf=_raf())
    with pytest.raises(GecersizIslemError):
        uc.execute(palet_id=palet.id)


def test_paletin_raf_bagli_degilse_depo_cozulemiyor():
    palet = _palet(raf_id=0)
    lot = MagicMock(urun_id=1)
    uc, *_ = _kur(palet=palet, lot=lot, urun=_urun(), raf=None)
    with pytest.raises(GecersizIslemError):
        uc.execute(palet_id=palet.id)


def test_farkli_depo_filtresi_yetki_hatasi():
    palet = _palet()
    lot = MagicMock(urun_id=1)
    raf = _raf(depo_id=1)
    uc, *_ = _kur(palet=palet, lot=lot, urun=_urun(), raf=raf)
    with pytest.raises(YetkisizIslemError):
        uc.execute(palet_id=palet.id, depo_id_filtresi=99)


def test_algoritma_none_donerse_uyari_doldurulur():
    palet = _palet()
    lot = MagicMock(urun_id=1)
    raf = _raf(depo_id=7)
    uc, *_ = _kur(palet=palet, lot=lot, urun=_urun(), raf=raf, oneri=None)

    sonuc = uc.execute(palet_id=palet.id)

    assert sonuc.depo_id == 7
    assert sonuc.onerilen is None
    assert sonuc.alternatifler == []
    assert sonuc.uyari is not None and "uygun raf" in sonuc.uyari.lower()


def test_oneri_donerse_dto_zenginlesir():
    palet = _palet()
    lot = MagicMock(urun_id=1)
    palet_rafi = _raf(id=10, depo_id=1)
    onerilen_raf = _raf(id=20, depo_id=1, zon_id=5, kapasite=10)
    alt_raf = _raf(id=21, depo_id=1, zon_id=5, kapasite=10)
    zon = Zon(id=5, depo_id=1, isim="Genel-A", tip=ZonTipi.GENEL, kod="GNL-A")

    oneri = YerlestirmeOnerisi(
        onerilen_raf=onerilen_raf,
        skor=82.5,
        alternatifler=[alt_raf],
        gerekce="Aynı üründen 2 palet mevcut, %40 dolu",
        bilesenler={"konsolidasyon": 80.0, "doluluk": 40.0, "fifo": 50.0, "zon_oncelik": 100.0},
        alternatif_detaylari=[
            AlternatifOneri(
                raf=alt_raf,
                skor=70.0,
                bilesenler={"konsolidasyon": 0.0, "doluluk": 30.0, "fifo": 50.0, "zon_oncelik": 100.0},
                gerekce="%30 dolu (3/10 slot), Skor: 70/100",
            ),
        ],
    )

    palet_repo = MagicMock()
    lot_repo = MagicMock()
    urun_repo = MagicMock()
    raf_repo = MagicMock()
    zon_repo = MagicMock()
    algoritma = MagicMock()

    palet_repo.getir_id_ile.return_value = palet
    # raf_repo.getir_id_ile sırasıyla: paletin rafı (depo çöz), önerilen raf detayı, alt raf detayı
    raf_repo.getir_id_ile.side_effect = lambda raf_id: {
        10: palet_rafi, 20: onerilen_raf, 21: alt_raf,
    }.get(raf_id)
    palet_repo.getir_hepsi.return_value = []  # bos_slot = kapasite
    lot_repo.getir_id_ile.return_value = lot
    urun_repo.getir_id_ile.return_value = _urun()
    zon_repo.getir_id_ile.return_value = zon
    algoritma.raf_oner.return_value = oneri

    uc = RafOneriSorgulaUseCase(
        palet_repo=palet_repo,
        lot_repo=lot_repo,
        urun_repo=urun_repo,
        raf_repo=raf_repo,
        zon_repo=zon_repo,
        algoritma=algoritma,
    )
    sonuc = uc.execute(palet_id=palet.id)

    assert sonuc.uyari is None
    assert sonuc.onerilen is not None
    assert sonuc.onerilen.raf_id == 20
    assert sonuc.onerilen.raf_kod == "RAF-020"
    assert sonuc.onerilen.zon_kod == "GNL-A"
    assert sonuc.onerilen.zon_tipi == ZonTipi.GENEL
    assert sonuc.onerilen.skor == 82.5
    assert sonuc.onerilen.bos_slot == 10
    assert "konsolidasyon" in sonuc.onerilen.bilesenler

    assert len(sonuc.alternatifler) == 1
    assert sonuc.alternatifler[0].raf_id == 21
    assert sonuc.alternatifler[0].skor == 70.0
