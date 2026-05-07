"""A* pathfinding — 4 yönlü grid, Manhattan heuristic.

MVP: tek robot perspektifinden plan; çakışma önleme kullanıcısının `engel_hucreler`
parametresiyle aktarılan diğer robot konumlarına dayanır (cooperative-light).
"""

from __future__ import annotations

import heapq
import itertools
from typing import Iterable

from app.core.entities.grid import Cell, Grid


def manhattan(a: Cell, b: Cell) -> int:
    return abs(a.x - b.x) + abs(a.y - b.y)


def a_star(
    grid: Grid,
    baslangic: Cell,
    hedef: Cell,
    engel_hucreler: Iterable[Cell] = (),
) -> list[Cell] | None:
    """Baslangic'tan hedefe rota — bulunamazsa None.

    `hedef` BOS/SARJ olmalıdır (raf hücreleri yaklaşma konumlarıyla hedeflenmelidir).
    `engel_hucreler` içindeki hücreler geçilemez sayılır (diğer robotların konumları).
    """
    if not grid.icinde_mi(baslangic) or not grid.icinde_mi(hedef):
        return None
    if not grid.gecilebilir_mi(hedef):
        return None
    if baslangic == hedef:
        return [baslangic]

    engel_set: set[Cell] = set(engel_hucreler)
    if baslangic in engel_set:
        engel_set = engel_set - {baslangic}  # robot kendi hücresinden çıkabilmeli

    # heap: (f, sayac, cell) — sayac tie-breaker (Cell karşılaştırılamaz)
    sayac = itertools.count()
    open_heap: list[tuple[int, int, Cell]] = []
    heapq.heappush(open_heap, (manhattan(baslangic, hedef), next(sayac), baslangic))

    g_score: dict[Cell, int] = {baslangic: 0}
    geldi: dict[Cell, Cell] = {}
    closed: set[Cell] = set()

    while open_heap:
        _, _, current = heapq.heappop(open_heap)
        if current in closed:
            continue
        if current == hedef:
            return _rotayi_kur(geldi, current)
        closed.add(current)

        for komsu in grid.komsular(current):
            if komsu in closed or komsu in engel_set:
                continue
            if not grid.gecilebilir_mi(komsu):
                continue
            tentative = g_score[current] + 1
            if tentative < g_score.get(komsu, 10**9):
                g_score[komsu] = tentative
                geldi[komsu] = current
                f = tentative + manhattan(komsu, hedef)
                heapq.heappush(open_heap, (f, next(sayac), komsu))

    return None


def _rotayi_kur(geldi: dict[Cell, Cell], hedef: Cell) -> list[Cell]:
    rota = [hedef]
    cur = hedef
    while cur in geldi:
        cur = geldi[cur]
        rota.append(cur)
    rota.reverse()
    return rota
