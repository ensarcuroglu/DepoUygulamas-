"""TickUseCase — robotları bir tick ilerletir, durum geçişlerini uygular.

Çıktı: bu tick'te oluşan event listesi (WS'e yayılmak üzere).
"""

from __future__ import annotations

from typing import Any

from app.core.entities.path import Path
from app.core.entities.robot import (
    BIRAKMA_TICK,
    YUKLEME_TICK,
    Robot,
    RobotDurum,
)
from app.core.exceptions import GecersizDurumGecisi
from app.core.services.rota_planlayici import (
    planla_ve_rezerve_et,
    rezervasyonu_birak,
)
from app.core.services.world import World

# Deadlock parametreleri (tick cinsinden)
DEADLOCK_REPLAN_ESIK = 4   # 4 tick hareketsiz → replan dene
DEADLOCK_HATA_ESIK = 16    # 16 tick hala hareketsiz → HATA_DURUYOR

_HAREKET_HALI = {
    RobotDurum.KAYNAGA_GIDIYOR,
    RobotDurum.TASIYOR,
}


class TickUseCase:
    def execute(self, world: World) -> list[dict[str, Any]]:
        world.tick_no += 1
        events: list[dict[str, Any]] = []
        # Geçmiş rezervasyonları temizle (memory leak guard)
        world.reservation_table.prune_before(world.tick_no)
        for robot in list(world.robotlar.values()):
            try:
                self._tick_robot(world, robot, events)
                self._deadlock_kontrol(world, robot, events)
            except GecersizDurumGecisi as e:
                robot.hata_durumuna_al()
                rezervasyonu_birak(world, robot)
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
            # Faz 3: TickLoop runtime bu event'i izliyor ve async olarak
            # WMS callback'i tetikliyor. Robot LOKALDE BOS'a dönmesine
            # rağmen WMS callback başarısız olursa görev WMS tarafında
            # kapanmaz; runtime fırsatçı retry yapmaz, log'a yazar.
            # (Eventual consistency tasarım kararı — bkz. plan §13.2.)
            gorev_id = robot.aktif_gorev_id
            gorev = world.aktif_gorevler.pop(gorev_id, None) if gorev_id else None
            if gorev is not None:
                gorev.tamamlanma_tick = world.tick_no
            robot.aktif_gorev_id = None
            robot.rota = None
            rezervasyonu_birak(world, robot)
            robot.durum_gecisi(RobotDurum.BOS)
            event = {
                "olay": "gorev_tamamlandi",
                "robot_id": robot.id,
                "gorev_id": gorev_id,
            }
            if gorev is not None:
                # WMS callback için gerekli alanlar (TickLoop runtime kullanır;
                # WS frontend ekstra alanları ignore eder)
                event.update(
                    {
                        "wms_gorev_id": gorev.wms_gorev_id,
                        "wms_gorev_tipi": gorev.wms_gorev_tipi,
                        "gerceklesen_raf_id": gorev.hedef_raf_id,
                        "sim_baslama_tick": gorev.baslama_tick,
                        "sim_tamamlanma_tick": gorev.tamamlanma_tick,
                    }
                )
            events.append(event)
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

    # ── deadlock tespiti + kurtarma (Faz 4) ──

    def _deadlock_kontrol(
        self, world: World, robot: Robot, events: list[dict[str, Any]]
    ) -> None:
        """Robot N tick boyunca aynı hücredeyse kurtar.

        - 4 tick stuck → rota'yı temizle, kooperatif replan dene.
        - 16 tick stuck → HATA_DURUYOR (operatör müdahalesi gerekli).
        """
        if robot.durum not in _HAREKET_HALI:
            world.robot_stuck.pop(robot.id, None)
            world.robot_son_konum[robot.id] = (robot.x, robot.y)
            return

        son = world.robot_son_konum.get(robot.id)
        konum = (robot.x, robot.y)
        if son != konum:
            world.robot_son_konum[robot.id] = konum
            world.robot_stuck[robot.id] = 0
            return

        stuck = world.robot_stuck.get(robot.id, 0) + 1
        world.robot_stuck[robot.id] = stuck

        if stuck == DEADLOCK_REPLAN_ESIK:
            self._replan_dene(world, robot, events)
        elif stuck >= DEADLOCK_HATA_ESIK:
            robot.hata_durumuna_al()
            rezervasyonu_birak(world, robot)
            world.robot_stuck.pop(robot.id, None)
            events.append(
                {
                    "olay": "deadlock_hata",
                    "robot_id": robot.id,
                    "neden": f"{DEADLOCK_HATA_ESIK} tick stuck",
                    "gorev_id": robot.aktif_gorev_id,
                }
            )

    def _replan_dene(
        self, world: World, robot: Robot, events: list[dict[str, Any]]
    ) -> None:
        gorev_id = robot.aktif_gorev_id
        if gorev_id is None:
            return
        gorev = world.aktif_gorevler.get(gorev_id)
        if gorev is None:
            return

        # Hedefi mevcut duruma göre seç
        if robot.durum == RobotDurum.KAYNAGA_GIDIYOR:
            hedef = world.grid.yaklasma_konumu(gorev.kaynak_raf_id)
        elif robot.durum == RobotDurum.TASIYOR:
            hedef = world.grid.yaklasma_konumu(gorev.hedef_raf_id)
        else:
            return

        # Eski rezervasyonları temizle, kooperatif replan
        rezervasyonu_birak(world, robot)
        rota = planla_ve_rezerve_et(world, robot, hedef)
        if rota is None:
            events.append(
                {
                    "olay": "deadlock_replan_basarisiz",
                    "robot_id": robot.id,
                    "gorev_id": gorev_id,
                }
            )
            return
        robot.rota = Path(cells=rota)
        events.append(
            {
                "olay": "deadlock_replan",
                "robot_id": robot.id,
                "gorev_id": gorev_id,
                "yeni_uzunluk": len(rota),
            }
        )
        events.append(
            {
                "olay": "rota_hesaplandi",
                "robot_id": robot.id,
                "rota": [[c.x, c.y] for c in rota],
            }
        )

    def _tasimaya_gecir(
        self,
        world: World,
        robot: Robot,
        events: list[dict[str, Any]],
    ) -> None:
        if robot.aktif_gorev_id is None:
            robot.hata_durumuna_al()
            rezervasyonu_birak(world, robot)
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
            rezervasyonu_birak(world, robot)
            events.append(
                {
                    "olay": "robot_hata",
                    "robot_id": robot.id,
                    "neden": "aktif gorev bulunamadi",
                }
            )
            return

        hedef = world.grid.yaklasma_konumu(gorev.hedef_raf_id)
        rota_cells = planla_ve_rezerve_et(world, robot, hedef)
        if rota_cells is None:
            robot.hata_durumuna_al()
            rezervasyonu_birak(world, robot)
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
