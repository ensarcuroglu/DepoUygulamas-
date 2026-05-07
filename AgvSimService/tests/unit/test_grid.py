"""Grid entity birim testleri."""

from __future__ import annotations

import pytest

from app.core.entities.grid import Cell, CellTipi, Grid, RafKonumu


def test_grid_olustur_dogru_boyut(basit_grid: Grid):
    assert basit_grid.genislik == 5
    assert basit_grid.yukseklik == 5
    assert basit_grid.cell_tipi(Cell(0, 0)) == CellTipi.BOS
    assert basit_grid.cell_tipi(Cell(1, 1)) == CellTipi.RAF


def test_gecilebilir_mi_raf_engel():
    g = Grid(
        genislik=2,
        yukseklik=2,
        hucreler=[
            [CellTipi.BOS, CellTipi.RAF],
            [CellTipi.SARJ, CellTipi.ENGEL],
        ],
        raflar={1: RafKonumu(raf_id=1, x=1, y=0, yaklasma_x=0, yaklasma_y=0)},
    )
    assert g.gecilebilir_mi(Cell(0, 0)) is True
    assert g.gecilebilir_mi(Cell(1, 0)) is False  # RAF
    assert g.gecilebilir_mi(Cell(0, 1)) is True   # SARJ
    assert g.gecilebilir_mi(Cell(1, 1)) is False  # ENGEL


def test_gecilebilir_mi_grid_disi():
    g = Grid(genislik=2, yukseklik=2, hucreler=[[CellTipi.BOS] * 2] * 2)
    assert g.gecilebilir_mi(Cell(-1, 0)) is False
    assert g.gecilebilir_mi(Cell(2, 0)) is False
    assert g.gecilebilir_mi(Cell(0, 5)) is False


def test_komsular_4_yonlu(basit_grid: Grid):
    komsular = list(basit_grid.komsular(Cell(2, 2)))
    assert set(komsular) == {Cell(3, 2), Cell(1, 2), Cell(2, 3), Cell(2, 1)}


def test_komsular_kose():
    g = Grid(genislik=3, yukseklik=3, hucreler=[[CellTipi.BOS] * 3 for _ in range(3)])
    komsular = list(g.komsular(Cell(0, 0)))
    assert set(komsular) == {Cell(1, 0), Cell(0, 1)}


def test_yaklasma_konumu(basit_grid: Grid):
    assert basit_grid.yaklasma_konumu(101) == Cell(1, 2)
    assert basit_grid.yaklasma_konumu(102) == Cell(3, 2)


def test_grid_tutarsiz_boyut_hata():
    with pytest.raises(ValueError):
        Grid(genislik=3, yukseklik=2, hucreler=[[CellTipi.BOS] * 3])  # 1 satır
    with pytest.raises(ValueError):
        Grid(genislik=3, yukseklik=2, hucreler=[[CellTipi.BOS] * 2, [CellTipi.BOS] * 3])
