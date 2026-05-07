"""A* pathfinding birim testleri."""

from __future__ import annotations

from app.core.entities.grid import Cell, CellTipi, Grid
from app.core.services.pathfinding import a_star, manhattan


def test_manhattan():
    assert manhattan(Cell(0, 0), Cell(3, 4)) == 7
    assert manhattan(Cell(2, 2), Cell(2, 2)) == 0


def test_a_star_ayni_hucre():
    g = Grid(genislik=3, yukseklik=3, hucreler=[[CellTipi.BOS] * 3 for _ in range(3)])
    rota = a_star(g, Cell(1, 1), Cell(1, 1))
    assert rota == [Cell(1, 1)]


def test_a_star_dogru_yol_acik_grid():
    g = Grid(genislik=5, yukseklik=5, hucreler=[[CellTipi.BOS] * 5 for _ in range(5)])
    rota = a_star(g, Cell(0, 0), Cell(4, 4))
    assert rota is not None
    assert rota[0] == Cell(0, 0)
    assert rota[-1] == Cell(4, 4)
    # Manhattan + 1 (başlangıç dahil)
    assert len(rota) == 9


def test_a_star_engel_etrafindan_dolasir():
    """5x5 grid, ortada bir RAF; A* etrafından geçmeli."""
    hucreler = [[CellTipi.BOS] * 5 for _ in range(5)]
    hucreler[2][2] = CellTipi.RAF
    g = Grid(genislik=5, yukseklik=5, hucreler=hucreler)
    rota = a_star(g, Cell(0, 2), Cell(4, 2))
    assert rota is not None
    assert Cell(2, 2) not in rota
    assert rota[0] == Cell(0, 2)
    assert rota[-1] == Cell(4, 2)


def test_a_star_ulasilamaz_hedef_none():
    """Hedef tamamen engellerle kuşatılı."""
    hucreler = [[CellTipi.BOS] * 5 for _ in range(5)]
    # (4,4)'ü kuşat
    hucreler[3][4] = CellTipi.ENGEL
    hucreler[4][3] = CellTipi.ENGEL
    g = Grid(genislik=5, yukseklik=5, hucreler=hucreler)
    rota = a_star(g, Cell(0, 0), Cell(4, 4))
    assert rota is None


def test_a_star_hedef_engel_tipindeyse_none():
    """Hedef RAF ise (geçilemez), A* None döner — caller yaklaşma cell'i geçmeli."""
    hucreler = [[CellTipi.BOS] * 3 for _ in range(3)]
    hucreler[1][1] = CellTipi.RAF
    g = Grid(genislik=3, yukseklik=3, hucreler=hucreler)
    assert a_star(g, Cell(0, 0), Cell(1, 1)) is None


def test_a_star_engel_hucreler_robotlari_bypass_eder():
    """Diğer robot konumlarını geçici engel olarak ekle, alternatif yol bulmalı."""
    g = Grid(genislik=5, yukseklik=3, hucreler=[[CellTipi.BOS] * 5 for _ in range(3)])
    # (1,1) ve (2,1) robotlarla dolu — orta satırı blokla, üst veya alttan geçmeli
    engeller = [Cell(1, 1), Cell(2, 1), Cell(3, 1)]
    rota = a_star(g, Cell(0, 1), Cell(4, 1), engel_hucreler=engeller)
    assert rota is not None
    assert all(c not in engeller for c in rota)


def test_a_star_baslangic_engel_iciyse_yine_calisir():
    """Robot kendi hücresinden çıkabilmeli — caller engel listesine kendini koyabilir."""
    g = Grid(genislik=3, yukseklik=3, hucreler=[[CellTipi.BOS] * 3 for _ in range(3)])
    rota = a_star(g, Cell(0, 0), Cell(2, 2), engel_hucreler=[Cell(0, 0)])
    assert rota is not None
    assert rota[0] == Cell(0, 0)
