"""Batarya simülasyonu birim testleri (Faz 5)."""

from __future__ import annotations

import pytest

from app.application.use_cases.tick import TickUseCase
from app.core.entities.grid import Cell, CellTipi, Grid
from app.core.entities.robot import Robot, RobotDurum
from app.core.services.batarya import (
    BATARYA_DOLUYOR,
    BATARYA_HAREKET,
    BATARYA_KRITIK,
    en_yakin_sarj,
    tick_uygula,
)
from app.core.services.world import World


@pytest.fixture
def sarjli_world() -> World:
    """3x3 grid, (0,0) SARJ, gerisi BOS."""
    hucreler = [[CellTipi.BOS] * 3 for _ in range(3)]
    hucreler[0][0] = CellTipi.SARJ
    g = Grid(
        genislik=3,
        yukseklik=3,
        hucreler=hucreler,
        sarj_konumlari=[Cell(0, 0)],
    )
    return World(grid=g)


def test_bos_durumda_sarj_disinda_azalir():
    r = Robot(id="R", x=1, y=1, batarya_yuzde=80.0, durum=RobotDurum.BOS)
    tick_uygula(r, CellTipi.BOS)
    assert r.batarya_yuzde < 80.0


def test_sarj_hucresinde_dolar():
    r = Robot(id="R", x=0, y=0, batarya_yuzde=50.0, durum=RobotDurum.BOS)
    tick_uygula(r, CellTipi.SARJ)
    assert r.batarya_yuzde == pytest.approx(50.0 + BATARYA_DOLUYOR)


def test_hareket_halinde_daha_hizli_azalir():
    bos = Robot(id="R1", x=1, y=1, batarya_yuzde=80.0, durum=RobotDurum.BOS)
    hareket = Robot(id="R2", x=1, y=1, batarya_yuzde=80.0, durum=RobotDurum.KAYNAGA_GIDIYOR)
    tick_uygula(bos, CellTipi.BOS)
    tick_uygula(hareket, CellTipi.BOS)
    # Hareket halindeki tüketim BOS'tan büyük
    assert (80.0 - hareket.batarya_yuzde) > (80.0 - bos.batarya_yuzde)


def test_dolum_100u_asmaz():
    r = Robot(id="R", x=0, y=0, batarya_yuzde=99.95, durum=RobotDurum.BOS)
    tick_uygula(r, CellTipi.SARJ)
    assert r.batarya_yuzde <= 100.0


def test_tukenme_0_altina_dusmez():
    r = Robot(
        id="R", x=1, y=1, batarya_yuzde=BATARYA_HAREKET / 2, durum=RobotDurum.KAYNAGA_GIDIYOR
    )
    tick_uygula(r, CellTipi.BOS)
    assert r.batarya_yuzde >= 0.0


def test_en_yakin_sarj_manhattan():
    r = Robot(id="R", x=5, y=5)
    sarjlar = [Cell(0, 0), Cell(4, 4), Cell(10, 10)]
    assert en_yakin_sarj(r, sarjlar) == Cell(4, 4)


def test_sarj_konumlari_yoksa_none():
    r = Robot(id="R", x=5, y=5)
    assert en_yakin_sarj(r, []) is None


def test_kritik_seviyede_otonom_sarja_donuyor(sarjli_world: World):
    """BOS robot bataryası kritik altına düşünce sarja_donuyor=True olmalı."""
    w = sarjli_world
    w.robot_ekle(
        Robot(id="R", x=2, y=2, durum=RobotDurum.BOS, batarya_yuzde=BATARYA_KRITIK + 0.05)
    )
    tick = TickUseCase()
    # Bir tick sonrası batarya kritik altına düşmüş olmalı (0.02% düşüş yetmez,
    # birkaç tick koşalım)
    for _ in range(20):
        tick.execute(w)

    r = w.robotlar["R"]
    # Kritik altına düştüyse sarja_donuyor=True olmuş veya zaten şarj noktasında
    assert r.batarya_yuzde < BATARYA_KRITIK or r.sarja_donuyor is True
    assert r.sarja_donuyor is True
