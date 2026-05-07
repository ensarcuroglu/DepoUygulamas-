"""Path (rota) value object."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.entities.grid import Cell


@dataclass
class Path:
    """Bir robot için hücre dizisi rotası.

    `cells[0]` = baslangıç, `cells[-1]` = hedef.
    `indis` ilerleyince mevcut konum `cells[indis]` olur.
    """

    cells: list[Cell]
    indis: int = 0

    def __post_init__(self) -> None:
        if not self.cells:
            raise ValueError("Path en az 1 hücre içermeli")

    @property
    def mevcut(self) -> Cell:
        return self.cells[self.indis]

    @property
    def hedef(self) -> Cell:
        return self.cells[-1]

    @property
    def kalan_uzunluk(self) -> int:
        return max(0, len(self.cells) - 1 - self.indis)

    def tamamlandi_mi(self) -> bool:
        return self.indis >= len(self.cells) - 1

    def sonraki(self) -> Cell | None:
        if self.tamamlandi_mi():
            return None
        return self.cells[self.indis + 1]

    def ilerle(self) -> None:
        if not self.tamamlandi_mi():
            self.indis += 1
