"""Kooperatif (zaman-uzay) A* + ReservationTable birim testleri."""

from __future__ import annotations

from app.core.entities.grid import Cell, CellTipi, Grid
from app.core.services.pathfinding import cooperative_a_star
from app.core.services.reservation_table import ReservationTable


def _bos_grid(genislik: int = 5, yukseklik: int = 3) -> Grid:
    return Grid(
        genislik=genislik,
        yukseklik=yukseklik,
        hucreler=[[CellTipi.BOS] * genislik for _ in range(yukseklik)],
    )


def test_kooperatif_bos_tablo_klasik_a_star_gibi():
    g = _bos_grid()
    rt = ReservationTable()
    rota = cooperative_a_star(
        g, Cell(0, 1), Cell(4, 1), current_tick=0, robot_id="R1", reservation_table=rt
    )
    assert rota is not None
    assert rota[0] == Cell(0, 1) and rota[-1] == Cell(4, 1)
    # 4 yön + WAIT yokken Manhattan eşit
    assert len(rota) == 5


def test_kooperatif_kafa_kafaya_cakismayi_engeller():
    """R1 (0,1)→(4,1), R2 (4,1)→(0,1) — koridor 1 satır geniş, swap engeli olmalı."""
    g = Grid(
        genislik=5,
        yukseklik=3,
        hucreler=[
            [CellTipi.ENGEL] * 5,
            [CellTipi.BOS] * 5,
            [CellTipi.ENGEL] * 5,
        ],
    )
    rt = ReservationTable()

    # R1 düz git
    r1 = cooperative_a_star(
        g, Cell(0, 1), Cell(4, 1), current_tick=0, robot_id="R1", reservation_table=rt
    )
    assert r1 is not None
    rt.reserve_path("R1", 0, r1)

    # R2 ters yön — sadece 1 satır olduğu için sıkışacak ve hedefe ulaşamaz
    # (max_horizon kısaysa). Klasik a_star alternatifi yok; CA*'da WAIT bile
    # yetmez, çünkü koridor tek satır. → None bekleniyor.
    r2 = cooperative_a_star(
        g,
        Cell(4, 1),
        Cell(0, 1),
        current_tick=0,
        robot_id="R2",
        reservation_table=rt,
        max_horizon=20,
    )
    assert r2 is None, "tek satır koridorda swap mümkün olmamalı"


def test_kooperatif_iki_satirli_koridor_bypass_eder():
    """2 satır koridorda R2 üstten/alttan dolaşarak rota bulabilmeli."""
    g = Grid(
        genislik=5,
        yukseklik=3,
        hucreler=[[CellTipi.BOS] * 5 for _ in range(3)],
    )
    rt = ReservationTable()

    r1 = cooperative_a_star(
        g, Cell(0, 1), Cell(4, 1), current_tick=0, robot_id="R1", reservation_table=rt
    )
    assert r1 is not None
    rt.reserve_path("R1", 0, r1)

    # R2 alternatif satırı tercih ederek başarmalı
    r2 = cooperative_a_star(
        g,
        Cell(4, 1),
        Cell(0, 1),
        current_tick=0,
        robot_id="R2",
        reservation_table=rt,
        max_horizon=30,
    )
    assert r2 is not None


def test_kooperatif_wait_eklenip_alternatif_zamanlama_bulur():
    """R1 iki cell rezerve etmiş. R2 başında 1-2 tick beklemeli, sonra geçmeli."""
    g = _bos_grid(genislik=4, yukseklik=1)
    rt = ReservationTable()
    # R1 (0,0) → (3,0)
    rt.reserve_path("R1", 0, [Cell(0, 0), Cell(1, 0), Cell(2, 0), Cell(3, 0)])

    # R2 başlamak için (1,0)'dan geçmek zorunda. Bekleyerek arka plan açılınca
    # geçebilir (wait_izinli=True).
    r2 = cooperative_a_star(
        g,
        Cell(0, 0),
        Cell(3, 0),
        current_tick=0,
        robot_id="R2",
        reservation_table=rt,
        max_horizon=50,
    )
    # Tek satırda öndeki R1 geçtikten sonra R2 takip edebilmeli (WAIT'lerle)
    assert r2 is not None
    assert r2[-1] == Cell(3, 0)


def test_reservation_table_release_robot_temizler():
    rt = ReservationTable()
    rt.reserve_path("R1", 5, [Cell(0, 0), Cell(1, 0)])
    assert rt.vertex_busy(Cell(0, 0), 5) is True
    rt.release_robot("R1")
    assert rt.vertex_busy(Cell(0, 0), 5) is False
    assert len(rt) == 0


def test_reservation_table_prune_before():
    rt = ReservationTable()
    rt.reserve_path("R1", 0, [Cell(0, 0), Cell(1, 0), Cell(2, 0)])
    assert len(rt) == 3
    rt.prune_before(2)
    # Sadece tick=2 olan kalmalı
    assert len(rt) == 1
    assert rt.vertex_busy(Cell(2, 0), 2) is True


def test_swap_blocked_dogru_tespit():
    rt = ReservationTable()
    # R1 t=0'da (1,0), t=1'de (0,0)
    rt.reserve_path("R1", 0, [Cell(1, 0), Cell(0, 0)])
    # R2 (0,0)→(1,0) yapmak isterse swap olur
    assert rt.swap_blocked(Cell(0, 0), Cell(1, 0), from_tick=0) is True
    # Aynı yön (R2 (0,0)→(0,1)) swap değil
    assert rt.swap_blocked(Cell(0, 0), Cell(0, 1), from_tick=0) is False
    # Robotun kendisi → except_robot ile filtrelenmiş, swap değil
    assert (
        rt.swap_blocked(Cell(0, 0), Cell(1, 0), from_tick=0, except_robot="R1") is False
    )
