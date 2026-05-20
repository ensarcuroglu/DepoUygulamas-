"""Palet runtime state yaşam döngüsü testleri.

Palet kayıtları AgvSimService'in görsel/event akışı içindir; DB'ye yazılmaz.
"""

from __future__ import annotations

import pytest

from app.application.use_cases.gorev_atama import GorevAtamaUseCase
from app.application.use_cases.tick import TickUseCase
from app.core.entities.agv_gorev import AgvGorev
from app.core.entities.grid import Cell, Grid
from app.core.entities.palet import PaletDurum
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
    w.robot_ekle(Robot(id="AGV-01", x=0, y=4, bekleme_konumu=Cell(0, 4)))
    return w


def _gorev_palet_id(palet_id: int | None = 7) -> AgvGorev:
    return AgvGorev(
        gorev_id="g-1",
        wms_gorev_id=42,
        wms_gorev_tipi="Yerlestirme",
        kaynak_raf_id=101,   # raf konumu (1,1), yaklasma (1,2)
        hedef_raf_id=102,    # raf konumu (3,3), yaklasma (3,2)
        palet_id=palet_id,
    )


def _tum_tick_calistir(world: World, n: int) -> list[dict]:
    tick = TickUseCase()
    atama = GorevAtamaUseCase()
    events: list[dict] = []
    for _ in range(n):
        events.extend(tick.execute(world))
        events.extend(atama.execute(world))
    return events


# ── Palet anahtarı ──


def test_palet_anahtari_palet_idli_gorevde_palet_id_bazli():
    g = _gorev_palet_id(palet_id=7)
    assert World.palet_anahtari(g) == "palet:7"


def test_palet_anahtari_palet_idsiz_gorevde_gorev_id_bazli():
    g = _gorev_palet_id(palet_id=None)
    assert World.palet_anahtari(g) == "gorev:g-1"


# ── Atama → KAYNAKTA_BEKLIYOR ──


def test_gorev_atandiginda_palet_kaynak_raf_konumunda_olusur(world: World):
    """Görev atandığında palet KAYNAKTA_BEKLIYOR durumda kaynak rafa konur."""
    world.gorev_kuyrugu.append(_gorev_palet_id())

    GorevAtamaUseCase().execute(world)

    palet = world.paletler["palet:7"]
    assert palet.durum == PaletDurum.KAYNAKTA_BEKLIYOR
    # Kaynak raf konumu: (1,1)
    assert (palet.x, palet.y) == (1, 1)
    assert palet.robot_id is None


def test_robot_kaynaga_giderken_palet_kaynakta_kalir(world: World):
    """Robot kaynağa varmadan palet KAYNAKTA_BEKLIYOR olmalı."""
    world.gorev_kuyrugu.append(_gorev_palet_id())

    # iter 1: atama; 2-3: KAYNAGA_GIDIYOR (henüz kaynağa varmadı)
    _tum_tick_calistir(world, 2)

    robot = world.robotlar["AGV-01"]
    palet = world.paletler["palet:7"]
    assert robot.durum == RobotDurum.KAYNAGA_GIDIYOR
    assert palet.durum == PaletDurum.KAYNAKTA_BEKLIYOR
    assert (palet.x, palet.y) == (1, 1)


# ── palet_alindi → ROBOT_UZERINDE ──


def test_palet_alindiktan_sonra_robot_uzerinde(world: World):
    """YUKLUYOR bitince palet ROBOT_UZERINDE durumuna geçmeli."""
    world.gorev_kuyrugu.append(_gorev_palet_id())

    # iter 1: atama; 2-4: KAYNAGA_GIDIYOR; 5-6: YUKLUYOR; iter 6 sonu: TASIYOR
    _tum_tick_calistir(world, 6)

    palet = world.paletler["palet:7"]
    robot = world.robotlar["AGV-01"]
    assert robot.durum == RobotDurum.TASIYOR
    assert palet.durum == PaletDurum.ROBOT_UZERINDE
    assert palet.robot_id == "AGV-01"


def test_palet_alindi_event_palet_key_tasir(world: World):
    world.gorev_kuyrugu.append(_gorev_palet_id())
    events = _tum_tick_calistir(world, 6)

    palet_alindi = next(e for e in events if e["olay"] == "palet_alindi")
    assert palet_alindi.get("palet_key") == "palet:7"


# ── ROBOT_UZERINDE: snapshot/delta x,y robotla senkron ──


def test_robot_uzerindeki_palet_snapshotta_robotun_konumunda(world: World):
    """ROBOT_UZERINDE palet payload'ında robotun x,y'sini taşımalı."""
    world.gorev_kuyrugu.append(_gorev_palet_id())
    # YUKLUYOR → TASIYOR sonrası bir tick ilerleme (iter 7 ilk ilerle).
    _tum_tick_calistir(world, 7)
    robot = world.robotlar["AGV-01"]
    delta = world.snapshot_delta()
    palet_p = next(p for p in delta["paletler"] if p["palet_key"] == "palet:7")
    assert palet_p["durum"] == "RobotUzerinde"
    assert (palet_p["x"], palet_p["y"]) == (robot.x, robot.y)


# ── palet_birakildi → HEDEFTE_BIRAKILDI ──


def test_palet_birakildiktan_sonra_hedefte_kalir(world: World):
    """BIRAKIYOR bitince palet HEDEFTE_BIRAKILDI olur, robot_id None."""
    world.gorev_kuyrugu.append(_gorev_palet_id())

    # Tam BIRAKIYOR bitiş tick'i: iter 10
    n = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK
    _tum_tick_calistir(world, n)

    palet = world.paletler["palet:7"]
    assert palet.durum == PaletDurum.HEDEFTE_BIRAKILDI
    assert palet.robot_id is None
    # Hedef raf konumu (3,3)
    assert (palet.x, palet.y) == (3, 3)


def test_palet_birakildi_event_palet_key_tasir(world: World):
    world.gorev_kuyrugu.append(_gorev_palet_id())
    n = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK
    events = _tum_tick_calistir(world, n)
    ev = next(e for e in events if e["olay"] == "palet_birakildi")
    assert ev.get("palet_key") == "palet:7"


# ── Park dönüşü: palet hedefte, robot üstünde değil ──


def test_park_donusunde_palet_hedefte_kalir_robot_uzerinde_degil(world: World):
    """Robot park dönüşündeyken palet hedef rafta kalmalı, robot üzerinde
    görünmemeli (robot_id None)."""
    world.gorev_kuyrugu.append(_gorev_palet_id())
    # Bildirim tick'i (görev kapanır, palet HEDEFTE) — sonra park dönüşü başlar.
    n = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK + 1 + 2  # +2 park dönüşü ilerleme
    _tum_tick_calistir(world, n)

    robot = world.robotlar["AGV-01"]
    palet = world.paletler["palet:7"]
    assert robot.durum == RobotDurum.BEKLEME_YERINE_DONUYOR
    assert palet.durum == PaletDurum.HEDEFTE_BIRAKILDI
    assert palet.robot_id is None
    assert (palet.x, palet.y) == (3, 3)


def test_park_donus_bitince_palet_hedefte_kalir(world: World):
    """Tam yaşam döngüsü: robot park'a vardığında palet hedef rafta sabit."""
    world.gorev_kuyrugu.append(_gorev_palet_id())
    toplam = 1 + 3 + YUKLEME_TICK + 2 + BIRAKMA_TICK + 1 + 5 + 5
    _tum_tick_calistir(world, toplam)

    robot = world.robotlar["AGV-01"]
    palet = world.paletler["palet:7"]
    assert robot.durum == RobotDurum.BOS
    assert (robot.x, robot.y) == (0, 4)
    assert palet.durum == PaletDurum.HEDEFTE_BIRAKILDI
    assert (palet.x, palet.y) == (3, 3)


# ── Snapshot/Delta yapısı ──


def test_snapshot_tam_paletler_alanini_yayinlar(world: World):
    world.gorev_kuyrugu.append(_gorev_palet_id())
    GorevAtamaUseCase().execute(world)
    snap = world.snapshot_tam()
    assert "paletler" in snap
    assert any(p["palet_key"] == "palet:7" for p in snap["paletler"])


def test_snapshot_delta_paletler_alanini_yayinlar(world: World):
    world.gorev_kuyrugu.append(_gorev_palet_id())
    GorevAtamaUseCase().execute(world)
    delta = world.snapshot_delta()
    assert "paletler" in delta
    palet_p = next(p for p in delta["paletler"] if p["palet_key"] == "palet:7")
    assert palet_p["durum"] == "KaynaktaBekliyor"
    assert palet_p["kaynak_raf_id"] == 101
    assert palet_p["hedef_raf_id"] == 102


def test_palet_id_yoksa_palet_key_gorev_id_bazli(world: World):
    """`palet_id` None gelirse palet_key gorev_id ile üretilir."""
    world.gorev_kuyrugu.append(_gorev_palet_id(palet_id=None))
    GorevAtamaUseCase().execute(world)
    assert "gorev:g-1" in world.paletler
