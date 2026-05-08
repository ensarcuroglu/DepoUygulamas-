"""RotaPlanlayici — kooperatif rota hesaplama (CA*) + güvenli fallback.

TickUseCase ve GorevAtamaUseCase tek bir noktadan rota planlasın diye
yardımcı fonksiyon. Sırayla:

1. `cooperative_a_star` ile zaman-uzay araması yap (rezervasyon tablosunu
   bilen). Diğer robotlar için vertex/swap çakışmasız bir plan döner.
2. Bulamazsa: klasik `a_star` ile diğer robotların ŞİMDİKİ konumlarını engel
   sayarak fallback dene (Faz 1-3 davranışı).
3. O da bulamazsa None.

Başarılı planda rezervasyon tablosu güncellenir.
"""

from __future__ import annotations

from typing import Optional

from app.core.entities.grid import Cell
from app.core.entities.robot import Robot
from app.core.services.pathfinding import a_star, cooperative_a_star
from app.core.services.world import World


def planla_ve_rezerve_et(
    world: World,
    robot: Robot,
    hedef: Cell,
    *,
    max_horizon: int = 200,
) -> Optional[list[Cell]]:
    """Robot için (mevcut hücre → hedef) rotayı planla, başarıysa rezerve et."""
    baslangic = Cell(robot.x, robot.y)

    # Diğer robotların ŞU ANKİ konumları statik engel sayılır — BOS robotların
    # rezervasyonu yoktur ama yine de çakışılmamalı. Hareket halindeki robotlar
    # zaten reservation_table üzerinden engellenir.
    statik = world.diger_robot_konumlari(robot)

    # Önce kooperatif planlama
    rota = cooperative_a_star(
        grid=world.grid,
        baslangic=baslangic,
        hedef=hedef,
        current_tick=world.tick_no,
        robot_id=robot.id,
        reservation_table=world.reservation_table,
        statik_engeller=statik,
        max_horizon=max_horizon,
    )
    if rota is not None:
        world.reservation_table.reserve_path(robot.id, world.tick_no, rota)
        return rota

    # Fallback: statik A* (diğer robotlar mevcut konumları kadar engel)
    diger = world.diger_robot_konumlari(robot)
    rota = a_star(world.grid, baslangic, hedef, engel_hucreler=diger)
    if rota is not None:
        world.reservation_table.reserve_path(robot.id, world.tick_no, rota)
    return rota


def rezervasyonu_birak(world: World, robot: Robot) -> None:
    world.reservation_table.release_robot(robot.id)
