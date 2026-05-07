"""World + TickUseCase + GorevAtamaUseCase entegrasyon testleri.

Bu testler asyncio kullanmaz — TickUseCase senkron, sadece World'deki state'i ilerletir.
"""

from __future__ import annotations

import pytest

from app.application.use_cases.gorev_atama import GorevAtamaUseCase
from app.application.use_cases.tick import TickUseCase
from app.core.entities.agv_gorev import AgvGorev
from app.core.entities.grid import Grid
from app.core.entities.robot import (
    BIRAKMA_TICK,
    YUKLEME_TICK,
    Robot,
    RobotDurum,
)
from app.core.services.world import World


@pytest.fixture
def world(basit_grid: Grid) -> World:
    w = World(grid=basit_grid)
    w.robot_ekle(Robot(id="AGV-01", x=0, y=4))  # şarj konumu
    return w


def _gorev() -> AgvGorev:
    return AgvGorev(
        gorev_id="g-1",
        wms_gorev_id=42,
        wms_gorev_tipi="Yerlestirme",
        kaynak_raf_id=101,  # yaklaşma (1,2)
        hedef_raf_id=102,   # yaklaşma (3,2)
    )


def _tum_tick_calistir(world: World, n: int) -> list[dict]:
    tick = TickUseCase()
    atama = GorevAtamaUseCase()
    events: list[dict] = []
    for _ in range(n):
        events.extend(tick.execute(world))
        events.extend(atama.execute(world))
    return events


def test_atama_use_case_bos_robota_gorev_atar(world: World):
    world.gorev_kuyrugu.append(_gorev())
    assert world.bos_robot_bul() is not None

    events = GorevAtamaUseCase().execute(world)

    olaylar = [e["olay"] for e in events]
    assert "gorev_atandi" in olaylar
    assert "rota_hesaplandi" in olaylar
    robot = world.robotlar["AGV-01"]
    assert robot.durum == RobotDurum.KAYNAGA_GIDIYOR
    assert robot.aktif_gorev_id == "g-1"
    assert "g-1" in world.aktif_gorevler
    assert world.gorev_kuyrugu == []


def test_atama_robot_yokken_gorev_kuyrukta_kalir(world: World):
    world.robotlar["AGV-01"].durum_gecisi(RobotDurum.KAYNAGA_GIDIYOR)
    world.gorev_kuyrugu.append(_gorev())

    events = GorevAtamaUseCase().execute(world)
    assert events == []
    assert len(world.gorev_kuyrugu) == 1


def test_full_lifecycle_gorev_tamamlanir(world: World):
    """Robot kaynaktan al → taşı → bırak → tamamla lifecycle'ını koşturur."""
    world.gorev_kuyrugu.append(_gorev())

    # Yeterince tick: kaynaga yol + yukleme + tasi yol + birakma + bildirim
    # Konum (0,4) → kaynak yaklaşma (1,2) ≈ 3 tick + YUKLEME_TICK
    # → hedef yaklaşma (3,2) ≈ 2 tick + BIRAKMA_TICK + 1 bildirim
    toplam_tick = 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK + 1 + 5  # +5 buffer
    _tum_tick_calistir(world, toplam_tick)

    robot = world.robotlar["AGV-01"]
    assert robot.durum == RobotDurum.BOS
    assert robot.aktif_gorev_id is None
    assert robot.x == 3 and robot.y == 2
    assert "g-1" not in world.aktif_gorevler
    assert world.gorev_kuyrugu == []


def test_tick_no_artiyor(world: World):
    tick = TickUseCase()
    tick.execute(world)
    tick.execute(world)
    assert world.tick_no == 2


def test_snapshot_delta_serializable(world: World):
    """Delta payload JSON-serializable olmalı (WS broadcast için kritik)."""
    import json

    delta = world.snapshot_delta()
    json.dumps(delta)  # Hata vermemeli
    assert "robotlar" in delta
    assert "tick_no" in delta


def test_snapshot_tam_grid_iceriyor(world: World):
    snap = world.snapshot_tam()
    assert "grid" in snap
    assert "raflar" in snap["grid"]
    assert len(snap["grid"]["raflar"]) == 2
