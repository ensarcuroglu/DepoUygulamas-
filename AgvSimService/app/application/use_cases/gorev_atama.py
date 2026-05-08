"""GorevAtamaUseCase — bekleyen kuyruktaki bir görevi boş robota atar."""

from __future__ import annotations

from typing import Any

from app.core.entities.path import Path
from app.core.entities.robot import RobotDurum
from app.core.services.rota_planlayici import planla_ve_rezerve_et
from app.core.services.world import World


class GorevAtamaUseCase:
    def execute(self, world: World) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if not world.gorev_kuyrugu:
            return events
        # Önceliğe göre sırala (1=en yüksek)
        world.gorev_kuyrugu.sort(key=lambda g: (g.oncelik, g.olusturma_ts))

        bos_robot = world.bos_robot_bul()
        if bos_robot is None:
            return events

        gorev = world.gorev_kuyrugu.pop(0)
        kaynak = world.grid.yaklasma_konumu(gorev.kaynak_raf_id)
        rota_cells = planla_ve_rezerve_et(world, bos_robot, kaynak)
        if rota_cells is None:
            world.gorev_kuyrugu.insert(0, gorev)
            events.append(
                {
                    "olay": "atama_basarisiz_rota_yok",
                    "gorev_id": gorev.gorev_id,
                }
            )
            return events

        bos_robot.rota = Path(cells=rota_cells)
        bos_robot.aktif_gorev_id = gorev.gorev_id
        bos_robot.durum_gecisi(RobotDurum.KAYNAGA_GIDIYOR)
        gorev.baslama_tick = world.tick_no
        world.aktif_gorevler[gorev.gorev_id] = gorev

        events.append(
            {
                "olay": "gorev_atandi",
                "robot_id": bos_robot.id,
                "gorev_id": gorev.gorev_id,
                "wms_gorev_id": gorev.wms_gorev_id,
            }
        )
        events.append(
            {
                "olay": "rota_hesaplandi",
                "robot_id": bos_robot.id,
                "rota": [[c.x, c.y] for c in rota_cells],
            }
        )
        return events
