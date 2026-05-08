"""Reservation table — kooperatif (CA*) pathfinding için zaman-uzay rezervasyonları.

Her robot rotasını planladığında, geçeceği (cell, mutlak_tick) çiftlerini bu
tabloya rezerve eder. Diğer robotların A* aramaları bu rezervasyonları engel
olarak görür.

İki tür çakışma modellenir:
- **Vertex conflict:** Aynı cell'de aynı tick'te iki robot.
- **Swap (edge) conflict:** İki robotun karşılıklı geçişi
  (R1: c1 → c2 ve R2: c2 → c1 aynı tick aralığında).

Tasarım: hafıza sınırlı kalsın diye `prune_before` ile geçmiş tick'ler periyodik
olarak temizlenir. Robot iptal edildiğinde `release_robot` çağrılır.
"""

from __future__ import annotations

from typing import Optional

from app.core.entities.grid import Cell


class ReservationTable:
    def __init__(self) -> None:
        # (cell, tick) -> robot_id
        self._vertex: dict[tuple[Cell, int], str] = {}
        # (cell, tick) -> robot_id  (robot bu tick'te bu cell'den ÇIKMIŞ olur)
        # Swap tespiti için yardımcı: R1 t'de c1, t+1'de c2 → R2 t'de c2, t+1'de c1 ise swap.
        self._owner_paths: dict[str, list[tuple[Cell, int]]] = {}

    # ── rezervasyon yönetimi ──

    def reserve_path(
        self, robot_id: str, current_tick: int, cells: list[Cell]
    ) -> None:
        """Robotun rotasını rezerve et.

        `cells[0]` = robotun current_tick'teki konumu (genelde mevcut hücre).
        `cells[i]` = robotun (current_tick + i) tick'indeki konumu.

        Aynı robot için önceki rezervasyonlar otomatik olarak temizlenir.
        """
        self.release_robot(robot_id)
        owner_path: list[tuple[Cell, int]] = []
        for i, cell in enumerate(cells):
            t = current_tick + i
            self._vertex[(cell, t)] = robot_id
            owner_path.append((cell, t))
        self._owner_paths[robot_id] = owner_path

    def release_robot(self, robot_id: str) -> None:
        """Robotun tüm rezervasyonlarını kaldır."""
        path = self._owner_paths.pop(robot_id, None)
        if not path:
            return
        for cell, t in path:
            owner = self._vertex.get((cell, t))
            if owner == robot_id:
                self._vertex.pop((cell, t), None)

    def prune_before(self, tick: int) -> None:
        """`tick`'ten küçük tüm rezervasyonları sil (geçmişi temizle)."""
        self._vertex = {k: v for k, v in self._vertex.items() if k[1] >= tick}
        for rid, path in list(self._owner_paths.items()):
            yeni = [(c, t) for c, t in path if t >= tick]
            if yeni:
                self._owner_paths[rid] = yeni
            else:
                self._owner_paths.pop(rid, None)

    # ── sorgu ──

    def vertex_busy(
        self, cell: Cell, tick: int, except_robot: Optional[str] = None
    ) -> bool:
        owner = self._vertex.get((cell, tick))
        if owner is None:
            return False
        return owner != except_robot

    def swap_blocked(
        self,
        from_cell: Cell,
        to_cell: Cell,
        from_tick: int,
        except_robot: Optional[str] = None,
    ) -> bool:
        """Bu robot from_tick'te from_cell'de, from_tick+1'de to_cell'de olacak.

        Çakışan robot from_tick'te to_cell'de, from_tick+1'de from_cell'de mi?
        """
        if from_cell == to_cell:
            return False
        owner_at_to_now = self._vertex.get((to_cell, from_tick))
        owner_at_from_next = self._vertex.get((from_cell, from_tick + 1))
        if owner_at_to_now is None or owner_at_from_next is None:
            return False
        if owner_at_to_now == except_robot or owner_at_from_next == except_robot:
            return False
        return owner_at_to_now == owner_at_from_next  # aynı diğer robot swap yapıyor

    def son_rezerve_tick(self, robot_id: str) -> Optional[int]:
        path = self._owner_paths.get(robot_id)
        if not path:
            return None
        return max(t for _, t in path)

    # ── tanılama / debug ──

    def __len__(self) -> int:  # toplam aktif rezervasyon sayısı
        return len(self._vertex)
