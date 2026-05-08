"""A* pathfinding — 4 yönlü grid, Manhattan heuristic.

İki varyant:
- `a_star`: klasik statik A*; `engel_hucreler` ile diğer robotların
  ŞİMDİKİ konumlarını engel sayar (Faz 1-3 davranışı, geri uyumluluk).
- `cooperative_a_star`: **zaman-uzay** A*; rezervasyon tablosunu okuyarak
  vertex + swap çakışmalarını engeller, gerekirse robotu bir tick `WAIT`
  ettirerek alternatif zamanlama bulur (Faz 4).
"""

from __future__ import annotations

import heapq
import itertools
from typing import Iterable, Optional

from app.core.entities.grid import Cell, Grid
from app.core.services.reservation_table import ReservationTable


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


# ─────────────────────────────────────────────────────────────────────────────
# Kooperatif A* (zaman-uzay arama)
# ─────────────────────────────────────────────────────────────────────────────


def cooperative_a_star(
    grid: Grid,
    baslangic: Cell,
    hedef: Cell,
    current_tick: int,
    robot_id: str,
    reservation_table: ReservationTable,
    statik_engeller: Iterable[Cell] = (),
    max_horizon: int = 200,
    wait_izinli: bool = True,
) -> Optional[list[Cell]]:
    """Rezervasyon tablosunu dikkate alan zaman-uzay A*.

    Düğüm: `(cell, t)` — t mutlak tick.
    Hareketler: 4 yön + (opsiyonel) WAIT (aynı hücrede 1 tick durma).
    Vertex çakışması (başka robot rezerve etmiş) ve swap çakışması engellenir.

    `max_horizon` arama uzayını sınırlar (vakit/uzay patlamasını önler).

    Dönen liste: `[baslangic, ..., hedef]` — `i`. eleman robotun
    `current_tick + i`'inci tick'te bulunacağı hücre. WAIT'ler aynı hücrenin
    art arda tekrarı olarak görünür; `Path` bunu doğal ilerleme olarak işler.
    """
    if not grid.icinde_mi(baslangic) or not grid.icinde_mi(hedef):
        return None
    if not grid.gecilebilir_mi(hedef):
        return None
    if baslangic == hedef:
        return [baslangic]

    statik_set: set[Cell] = set(statik_engeller) - {baslangic}

    sayac = itertools.count()
    open_heap: list[tuple[int, int, Cell, int]] = []
    h0 = manhattan(baslangic, hedef)
    heapq.heappush(open_heap, (h0, next(sayac), baslangic, 0))

    g_score: dict[tuple[Cell, int], int] = {(baslangic, current_tick): 0}
    geldi: dict[tuple[Cell, int], tuple[Cell, int]] = {}

    while open_heap:
        _, _, cur_cell, step = heapq.heappop(open_heap)
        cur_t = current_tick + step
        if cur_cell == hedef:
            # Yolu (cell,t) düğümlerinden geri kur, sadece cell'leri döndür
            yol_dugumler: list[tuple[Cell, int]] = [(cur_cell, cur_t)]
            d = (cur_cell, cur_t)
            while d in geldi:
                d = geldi[d]
                yol_dugumler.append(d)
            yol_dugumler.reverse()
            return [c for c, _ in yol_dugumler]

        if step >= max_horizon:
            continue

        next_t = cur_t + 1

        # Komşu adayları + isteğe bağlı WAIT
        adaylar: list[Cell] = list(grid.komsular(cur_cell))
        if wait_izinli:
            adaylar.append(cur_cell)

        for komsu in adaylar:
            if komsu != cur_cell:
                if komsu in statik_set:
                    continue
                if not grid.gecilebilir_mi(komsu):
                    continue
            # Vertex çakışması: başka robot next_t'de komsu'yu rezerve etmişse
            if reservation_table.vertex_busy(komsu, next_t, except_robot=robot_id):
                continue
            # Swap çakışması: başka robot şimdi komsu'da, sonra cur_cell'e gidecek
            if reservation_table.swap_blocked(
                from_cell=cur_cell,
                to_cell=komsu,
                from_tick=cur_t,
                except_robot=robot_id,
            ):
                continue

            tentative = g_score[(cur_cell, cur_t)] + 1
            anahtar = (komsu, next_t)
            if tentative < g_score.get(anahtar, 10**9):
                g_score[anahtar] = tentative
                geldi[anahtar] = (cur_cell, cur_t)
                f = tentative + manhattan(komsu, hedef)
                heapq.heappush(open_heap, (f, next(sayac), komsu, step + 1))

    return None
