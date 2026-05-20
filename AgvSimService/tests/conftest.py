"""pytest fixtures."""

from __future__ import annotations

import pytest

from app.core.entities.grid import Cell, CellTipi, Grid, RafKonumu


@pytest.fixture
def basit_grid() -> Grid:
    """5x5 boş grid, 2 raf (1,1) ve (3,3); yaklaşma hücreleri (1,2) ve (3,2)."""
    genislik, yukseklik = 5, 5
    hucreler = [[CellTipi.BOS for _ in range(genislik)] for _ in range(yukseklik)]
    hucreler[1][1] = CellTipi.RAF
    hucreler[3][3] = CellTipi.RAF
    raflar = {
        101: RafKonumu(raf_id=101, x=1, y=1, yaklasma_x=1, yaklasma_y=2, kod="A-01"),
        102: RafKonumu(raf_id=102, x=3, y=3, yaklasma_x=3, yaklasma_y=2, kod="A-02"),
    }
    return Grid(
        genislik=genislik,
        yukseklik=yukseklik,
        hucreler=hucreler,
        raflar=raflar,
        sarj_konumlari=[Cell(0, 4)],
        bekleme_konumlari=[Cell(0, 4)],
    )
