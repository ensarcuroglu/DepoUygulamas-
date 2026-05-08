"""World — in-memory simülasyon dünyası (process-local singleton)."""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from app.core.entities.agv_gorev import AgvGorev
from app.core.entities.grid import Grid
from app.core.entities.robot import Robot, RobotDurum
from app.core.services.reservation_table import ReservationTable


class World:
    """Tüm in-flight AGV state'i. Tek süreç zorunlu (replica yok).

    `lock` tick loop ve HTTP handler'lar arasındaki yarış koşullarını engeller.
    """

    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.robotlar: dict[str, Robot] = {}
        self.gorev_kuyrugu: list[AgvGorev] = []
        self.aktif_gorevler: dict[str, AgvGorev] = {}
        self.tick_no: int = 0
        self.lock: asyncio.Lock = asyncio.Lock()
        # Faz 4: kooperatif zaman-uzay rezervasyonları
        self.reservation_table = ReservationTable()
        # Robot bazlı deadlock takibi: stuck_tick_count, son_konum
        self.robot_stuck: dict[str, int] = {}
        self.robot_son_konum: dict[str, tuple[int, int]] = {}

    def robot_ekle(self, robot: Robot) -> None:
        if robot.id in self.robotlar:
            raise ValueError(f"Robot {robot.id} zaten var")
        self.robotlar[robot.id] = robot

    def bos_robot_bul(self) -> Optional[Robot]:
        for r in self.robotlar.values():
            if r.durum == RobotDurum.BOS:
                return r
        return None

    def diger_robot_konumlari(self, kendisi: Robot) -> set:
        from app.core.entities.grid import Cell
        return {Cell(r.x, r.y) for r in self.robotlar.values() if r.id != kendisi.id}

    def robot_dict_listesi(self) -> list[dict]:
        return [
            {
                "id": r.id,
                "x": r.x,
                "y": r.y,
                "durum": r.durum.value,
                "yon": r.yon.value,
                "gorev_id": r.aktif_gorev_id,
                "rota_kalan": r.rota.kalan_uzunluk if r.rota else 0,
            }
            for r in self.robotlar.values()
        ]

    def snapshot_tam(self) -> dict:
        """WS bağlantısının ilk mesajı — grid + tüm robotlar."""
        return {
            "tick_no": self.tick_no,
            "ts": time.time(),
            "grid": {
                "genislik": self.grid.genislik,
                "yukseklik": self.grid.yukseklik,
                "raflar": [
                    {
                        "raf_id": r.raf_id,
                        "x": r.x,
                        "y": r.y,
                        "yaklasma_x": r.yaklasma_x,
                        "yaklasma_y": r.yaklasma_y,
                        "kod": r.kod,
                    }
                    for r in self.grid.raflar.values()
                ],
                "sarj_konumlari": [
                    {"x": c.x, "y": c.y} for c in self.grid.sarj_konumlari
                ],
            },
            "robotlar": self.robot_dict_listesi(),
        }

    def snapshot_delta(self) -> dict:
        """Her tick'te WS'e gönderilen delta — sadece dinamik state."""
        return {
            "tick_no": self.tick_no,
            "ts": time.time(),
            "robotlar": self.robot_dict_listesi(),
            "kuyruk_uzunlugu": len(self.gorev_kuyrugu),
            "aktif_gorev_sayisi": len(self.aktif_gorevler),
        }


# ── Process-local singleton (lifespan'de set edilir) ──

_WORLD: Optional[World] = None


def set_world(world: World) -> None:
    global _WORLD
    _WORLD = world


def get_world() -> World:
    if _WORLD is None:
        raise RuntimeError("World henüz başlatılmadı (lifespan beklenir)")
    return _WORLD


def reset_world_for_test() -> None:
    """Sadece test ortamı için."""
    global _WORLD
    _WORLD = None
