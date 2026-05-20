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
    from app.core.entities.grid import Cell

    w = World(grid=basit_grid)
    # Robot şarj/park konumunda başlar; bekleme_konumu da bu hücre.
    w.robot_ekle(
        Robot(id="AGV-01", x=0, y=4, bekleme_konumu=Cell(0, 4))
    )
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
    """Robot kaynaktan al → taşı → bırak → bildirim → parka dön → BOS."""
    world.gorev_kuyrugu.append(_gorev())

    # iter 1: atama; 2-4: KAYNAGA_GIDIYOR; 5-6: YUKLUYOR; 7-8: TASIYOR;
    # 9-10: BIRAKIYOR; 11: TAMAMLANDI_BILDIRIM (parka_yonlendir);
    # 12-16: BEKLEME_YERINE_DONUYOR (5 tick (3,2)→(0,4)); +buffer.
    toplam_tick = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK + 1 + 5 + 5
    _tum_tick_calistir(world, toplam_tick)

    robot = world.robotlar["AGV-01"]
    assert robot.durum == RobotDurum.BOS
    assert robot.aktif_gorev_id is None
    # Robot artık bırakma noktasında değil; park konumunda olmalı.
    assert (robot.x, robot.y) == (0, 4)
    assert "g-1" not in world.aktif_gorevler
    assert world.gorev_kuyrugu == []


def test_gorev_tamamlandi_event_park_donmeden_yayinlanir(world: World):
    """`gorev_tamamlandi` event'i (WMS callback fire eden) park dönüşünden
    önce yayınlanmalı; robot fiziksel hazırlık ise ancak park varışında BOS."""
    world.gorev_kuyrugu.append(_gorev())

    # iter 1: atama; 2-4: KAYNAGA_GIDIYOR; 5-6: YUKLUYOR; 7-8: TASIYOR;
    # 9-10: BIRAKIYOR; iter 11: TAMAMLANDI_BILDIRIM → gorev_tamamlandi + parka_yonlendir
    n = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK + 1
    events = _tum_tick_calistir(world, n)

    tipler = [e["olay"] for e in events]
    assert "gorev_tamamlandi" in tipler
    # gorev_tamamlandi event'i WMS callback için gerekli alanları taşımalı
    ev = next(e for e in events if e["olay"] == "gorev_tamamlandi")
    assert ev.get("wms_gorev_id") == 42

    robot = world.robotlar["AGV-01"]
    # Bildirim tick'inde park dönüşüne geçmiş olmalı (eğer park hücresinde
    # değilse). (3,2) park konumu değil → BEKLEME_YERINE_DONUYOR beklenir.
    assert robot.durum == RobotDurum.BEKLEME_YERINE_DONUYOR
    assert robot.aktif_gorev_id is None


def test_park_donus_sirasinda_yeni_gorev_alinmaz(world: World):
    """Robot park dönüşündeyken (BOS değil) bos_robot_bul None döndürmeli."""
    world.gorev_kuyrugu.append(_gorev())
    # İlk görevin bırakma+bildirim tick'ine kadar koştur.
    n = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK + 1
    _tum_tick_calistir(world, n)
    robot = world.robotlar["AGV-01"]
    assert robot.durum == RobotDurum.BEKLEME_YERINE_DONUYOR
    # Yeni görev kuyruğa eklense bile bos_robot_bul None olmalı
    assert world.bos_robot_bul() is None


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
    # Park konumları snapshot'ta yer almalı (frontend görselleştirir)
    assert "bekleme_konumlari" in snap["grid"]


def test_snapshot_delta_bekleme_konumunu_yayinlar(world: World):
    delta = world.snapshot_delta()
    robotlar = delta["robotlar"]
    assert robotlar[0]["bekleme_konumu"] == [0, 4]


def test_bos_park_bul_baska_robot_uzerindeyse_alternatif_secer(
    basit_grid: Grid,
):
    from app.core.entities.grid import Cell

    # İki park konumu olan grid
    basit_grid.bekleme_konumlari = [Cell(0, 4), Cell(4, 4)]
    w = World(grid=basit_grid)
    w.robot_ekle(Robot(id="A", x=0, y=4, bekleme_konumu=Cell(0, 4)))
    w.robot_ekle(Robot(id="B", x=2, y=2, bekleme_konumu=Cell(0, 4)))

    # B kendi atanmış park'ına dönmek isterse (0,4)'de A var → (4,4) seçilmeli
    hedef = w.bos_park_bul(w.robotlar["B"])
    assert hedef == Cell(4, 4)


def test_parka_donus_event_yayinlanir_ve_robot_bos_olur(world: World):
    """Tam yaşam döngüsü sonrası robot fiziksel olarak park konumunda BOS."""
    world.gorev_kuyrugu.append(_gorev())
    toplam = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK + 1 + 5 + 5
    events = _tum_tick_calistir(world, toplam)

    olaylar = [e["olay"] for e in events]
    assert "parka_donuyor" in olaylar
    assert "bekleme_yerine_vardi" in olaylar

    robot = world.robotlar["AGV-01"]
    assert robot.durum == RobotDurum.BOS
    assert (robot.x, robot.y) == (0, 4)
