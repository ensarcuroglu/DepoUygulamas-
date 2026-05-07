"""Robot state machine birim testleri."""

from __future__ import annotations

import pytest

from app.core.entities.path import Path
from app.core.entities.grid import Cell
from app.core.entities.robot import Robot, RobotDurum, Yon
from app.core.exceptions import GecersizDurumGecisi


def _yeni_robot() -> Robot:
    return Robot(id="AGV-T", x=0, y=0)


def test_robot_default_durum_bos():
    r = _yeni_robot()
    assert r.durum == RobotDurum.BOS
    assert r.yon == Yon.KUZEY
    assert r.rota is None


def test_normal_akis_durum_gecisi_dogru():
    r = _yeni_robot()
    r.durum_gecisi(RobotDurum.KAYNAGA_GIDIYOR)
    r.durum_gecisi(RobotDurum.YUKLUYOR)
    r.durum_gecisi(RobotDurum.TASIYOR)
    r.durum_gecisi(RobotDurum.BIRAKIYOR)
    r.durum_gecisi(RobotDurum.TAMAMLANDI_BILDIRIM)
    r.durum_gecisi(RobotDurum.BOS)
    assert r.durum == RobotDurum.BOS


def test_gecersiz_gecis_hata_firlatir():
    r = _yeni_robot()
    with pytest.raises(GecersizDurumGecisi):
        r.durum_gecisi(RobotDurum.TASIYOR)  # BOS → TASIYOR yasak

    r.durum_gecisi(RobotDurum.KAYNAGA_GIDIYOR)
    with pytest.raises(GecersizDurumGecisi):
        r.durum_gecisi(RobotDurum.BOS)  # KAYNAGA_GIDIYOR → BOS yasak


def test_her_durumdan_hata_duruyora_gecilebilir():
    for baslangic in (
        RobotDurum.KAYNAGA_GIDIYOR,
        RobotDurum.YUKLUYOR,
        RobotDurum.TASIYOR,
        RobotDurum.BIRAKIYOR,
        RobotDurum.TAMAMLANDI_BILDIRIM,
    ):
        r = _yeni_robot()
        r.durum = baslangic
        r.durum_gecisi(RobotDurum.HATA_DURUYOR)
        assert r.durum == RobotDurum.HATA_DURUYOR


def test_hata_duruyordan_sifirla():
    r = _yeni_robot()
    r.aktif_gorev_id = "g-1"
    r.rota = Path(cells=[Cell(0, 0), Cell(1, 0)])
    r.hata_durumuna_al()
    assert r.durum == RobotDurum.HATA_DURUYOR
    r.sifirla()
    assert r.durum == RobotDurum.BOS
    assert r.aktif_gorev_id is None
    assert r.rota is None


def test_sifirla_yanlis_durumdan_hata_firlatir():
    r = _yeni_robot()
    with pytest.raises(GecersizDurumGecisi):
        r.sifirla()


def test_yon_guncelle():
    r = _yeni_robot()
    r.yon_guncelle(1, 0)
    assert r.yon == Yon.DOGU
    r.yon_guncelle(0, -1)
    assert r.yon == Yon.KUZEY
    r.yon_guncelle(0, 1)
    assert r.yon == Yon.GUNEY
    r.yon_guncelle(-1, 0)
    assert r.yon == Yon.BATI


def test_yon_guncelle_dura_kaldigi_yon_korunur():
    r = _yeni_robot()
    r.yon = Yon.DOGU
    r.yon_guncelle(0, 0)  # tanımsız delta
    assert r.yon == Yon.DOGU
