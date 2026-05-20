"""Grid (depo haritası) domain entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterator


class CellTipi(str, Enum):
    BOS = "BOS"        # Geçilebilir koridor
    RAF = "RAF"        # Engel; yaklaşma hücresi üzerinden hedef
    ENGEL = "ENGEL"    # Statik engel (sütun, duvar)
    SARJ = "SARJ"      # Şarj noktası (geçilebilir)


@dataclass(frozen=True)
class Cell:
    x: int
    y: int


@dataclass(frozen=True)
class RafKonumu:
    raf_id: int
    x: int
    y: int
    yaklasma_x: int
    yaklasma_y: int
    kod: str = ""

    @property
    def yaklasma(self) -> Cell:
        return Cell(self.yaklasma_x, self.yaklasma_y)

    @property
    def konum(self) -> Cell:
        return Cell(self.x, self.y)


@dataclass
class Grid:
    """2D grid harita.

    `hucreler` 2 boyutlu liste — `hucreler[y][x]`.
    Pathfinding `gecilebilir_mi` ile koridor/şarj hücrelerini geçilebilir,
    raf/engel hücrelerini engel olarak görür.
    """

    genislik: int
    yukseklik: int
    hucreler: list[list[CellTipi]]
    raflar: dict[int, RafKonumu] = field(default_factory=dict)
    sarj_konumlari: list[Cell] = field(default_factory=list)
    # Park / bekleme hücreleri (BOS tipinde olmalı). Robotlar görev sonrası
    # buralardan birine geri döner. SARJ konumları ile çakışabilir; çakışırsa
    # ikisi de geçerli kabul edilir.
    bekleme_konumlari: list[Cell] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.hucreler) != self.yukseklik:
            raise ValueError(
                f"hucreler satır sayısı {len(self.hucreler)} ≠ yukseklik {self.yukseklik}"
            )
        for y, satir in enumerate(self.hucreler):
            if len(satir) != self.genislik:
                raise ValueError(
                    f"hucreler[{y}] sütun sayısı {len(satir)} ≠ genislik {self.genislik}"
                )

    def icinde_mi(self, cell: Cell) -> bool:
        return 0 <= cell.x < self.genislik and 0 <= cell.y < self.yukseklik

    def cell_tipi(self, cell: Cell) -> CellTipi:
        if not self.icinde_mi(cell):
            raise ValueError(f"Cell grid dışında: {cell}")
        return self.hucreler[cell.y][cell.x]

    def gecilebilir_mi(self, cell: Cell) -> bool:
        if not self.icinde_mi(cell):
            return False
        return self.hucreler[cell.y][cell.x] in (CellTipi.BOS, CellTipi.SARJ)

    def komsular(self, cell: Cell) -> Iterator[Cell]:
        """4 yönlü komşuları döndür (grid içi olanlar)."""
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            komsu = Cell(cell.x + dx, cell.y + dy)
            if self.icinde_mi(komsu):
                yield komsu

    def yaklasma_konumu(self, raf_id: int) -> Cell:
        return self.raflar[raf_id].yaklasma
