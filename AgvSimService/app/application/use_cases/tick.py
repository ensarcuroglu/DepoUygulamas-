"""TickUseCase — robotları bir tick ilerletir, durum geçişlerini uygular.

Çıktı: bu tick'te oluşan event listesi (WS'e yayılmak üzere).
"""

from __future__ import annotations

from typing import Any

from app.core.entities.grid import Cell
from app.core.entities.path import Path
from app.core.entities.robot import (
    BIRAKMA_TICK,
    YUKLEME_TICK,
    Robot,
    RobotDurum,
)
from app.core.exceptions import GecersizDurumGecisi
from app.core.services.pathfinding import a_star
from app.core.services.world import World


class TickUseCase:
    def execute(self, world: World) -> list[dict[str, Any]]:
        world.tick_no += 1
        events: list[dict[str, Any]] = []
        for robot in list(world.robotlar.values()):
            try:
                self._tick_robot(world, robot, events)
            except GecersizDurumGecisi as e:
                robot.hata_durumuna_al()
                events.append(
                    {
                        "olay": "robot_hata",
                        "robot_id": robot.id,
                        "neden": str(e),
                    }
                )
        return events

    # ── private ──

    def _tick_robot(
        self, world: World, robot: Robot, events: list[dict[str, Any]]
    ) -> None:
        d = robot.durum
        if d in (RobotDurum.BOS, RobotDurum.HATA_DURUYOR):
            return

        if d == RobotDurum.KAYNAGA_GIDIYOR:
            self._ilerle(robot)
            if robot.rota and robot.rota.tamamlandi_mi():
                robot.bekleme_kalani = YUKLEME_TICK
                robot.durum_gecisi(RobotDurum.YUKLUYOR)
                events.append({"olay": "kaynaga_vardi", "robot_id": robot.id})
            return

        if d == RobotDurum.YUKLUYOR:
            robot.bekleme_kalani -= 1
            if robot.bekleme_kalani > 0:
                return
            self._tasimaya_gecir(world, robot, events)
            return

        if d == RobotDurum.TASIYOR:
            self._ilerle(robot)
            if robot.rota and robot.rota.tamamlandi_mi():
                robot.bekleme_kalani = BIRAKMA_TICK
                robot.durum_gecisi(RobotDurum.BIRAKIYOR)
                events.append({"olay": "hedefe_vardi", "robot_id": robot.id})
            return

        if d == RobotDurum.BIRAKIYOR:
            robot.bekleme_kalani -= 1
            if robot.bekleme_kalani > 0:
                return
            robot.durum_gecisi(RobotDurum.TAMAMLANDI_BILDIRIM)
            events.append(
                {
                    "olay": "palet_birakildi",
                    "robot_id": robot.id,
                    "gorev_id": robot.aktif_gorev_id,
                }
            )
            return

        if d == RobotDurum.TAMAMLANDI_BILDIRIM:
            # Faz 3: WMS callback burada tetiklenecek (asyncio.create_task).
            # MVP: doğrudan BOS'a dön.
            gorev_id = robot.aktif_gorev_id
            gorev = world.aktif_gorevler.pop(gorev_id, None) if gorev_id else None
            if gorev is not None:
                gorev.tamamlanma_tick = world.tick_no
            robot.aktif_gorev_id = None
            robot.rota = None
            robot.durum_gecisi(RobotDurum.BOS)
            events.append(
                {
                    "olay": "gorev_tamamlandi",
                    "robot_id": robot.id,
                    "gorev_id": gorev_id,
                }
            )
            return

    def _ilerle(self, robot: Robot) -> None:
        if robot.rota is None or robot.rota.tamamlandi_mi():
            return
        sonraki = robot.rota.sonraki()
        if sonraki is None:
            return
        dx, dy = sonraki.x - robot.x, sonraki.y - robot.y
        robot.yon_guncelle(dx, dy)
        robot.x, robot.y = sonraki.x, sonraki.y
        robot.rota.ilerle()

    def _tasimaya_gecir(
        self,
        world: World,
        robot: Robot,
        events: list[dict[str, Any]],
    ) -> None:
        if robot.aktif_gorev_id is None:
            robot.hata_durumuna_al()
            events.append(
                {
                    "olay": "robot_hata",
                    "robot_id": robot.id,
                    "neden": "yukluyor durumunda aktif gorev yok",
                }
            )
            return
        gorev = world.aktif_gorevler.get(robot.aktif_gorev_id)
        if gorev is None:
            robot.hata_durumuna_al()
            events.append(
                {
                    "olay": "robot_hata",
                    "robot_id": robot.id,
                    "neden": "aktif gorev bulunamadi",
                }
            )
            return

        hedef = world.grid.yaklasma_konumu(gorev.hedef_raf_id)
        engeller = world.diger_robot_konumlari(robot)
        rota_cells = a_star(world.grid, Cell(robot.x, robot.y), hedef, engeller)
        if rota_cells is None:
            robot.hata_durumuna_al()
            events.append(
                {
                    "olay": "rota_bulunamadi",
                    "robot_id": robot.id,
                    "gorev_id": robot.aktif_gorev_id,
                }
            )
            return

        robot.rota = Path(cells=rota_cells)
        robot.durum_gecisi(RobotDurum.TASIYOR)
        events.append({"olay": "palet_alindi", "robot_id": robot.id})
        events.append(
            {
                "olay": "rota_hesaplandi",
                "robot_id": robot.id,
                "rota": [[c.x, c.y] for c in rota_cells],
            }
        )
