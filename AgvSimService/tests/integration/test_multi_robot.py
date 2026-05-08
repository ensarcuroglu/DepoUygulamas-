"""Çoklu robot smoke + yük testi.

Gerçek depo gridi (data/depo_1_grid.json) üzerinde 4 robot, paralel görev
trafiği koşar; tüm görevler tamamlanmalı, hiçbir robot HATA_DURUYOR'a
düşmemeli.
"""

from __future__ import annotations

import pytest

from app.application.use_cases.gorev_atama import GorevAtamaUseCase
from app.application.use_cases.tick import TickUseCase
from app.core.entities.agv_gorev import AgvGorev
from app.core.entities.robot import Robot, RobotDurum
from app.core.services.world import World
from app.infrastructure.grid_loader import gridi_jsondan_yukle


@pytest.fixture
def real_world() -> World:
    """data/depo_1_grid.json'dan yüklü 4 robotlu world."""
    grid = gridi_jsondan_yukle("data/depo_1_grid.json")
    w = World(grid=grid)
    konumlar = [
        ("AGV-01", 0, 11),
        ("AGV-02", 1, 11),
        ("AGV-03", 2, 11),
        ("AGV-04", 3, 11),
    ]
    for rid, x, y in konumlar:
        w.robot_ekle(Robot(id=rid, x=x, y=y))
    return w


def test_4_robot_paralel_8_gorev_hicbir_robot_hata_dusmez(real_world: World):
    """4 robot, 8 görev (peş peşe atanır) — hepsi 600 tick içinde tamamlanmalı."""
    w = real_world
    gorev_ciftleri = [
        (101, 207),
        (102, 206),
        (103, 205),
        (104, 204),
        (203, 105),
        (202, 106),
        (201, 107),
        (107, 101),
    ]
    for i, (kaynak, hedef) in enumerate(gorev_ciftleri, start=1):
        w.gorev_kuyrugu.append(
            AgvGorev(
                gorev_id=f"g-{i}",
                wms_gorev_id=1000 + i,
                wms_gorev_tipi="Yerlestirme",
                kaynak_raf_id=kaynak,
                hedef_raf_id=hedef,
            )
        )

    tick = TickUseCase()
    atama = GorevAtamaUseCase()
    olaylar: list[dict] = []
    MAX_TICK = 600
    for _ in range(MAX_TICK):
        olaylar.extend(tick.execute(w))
        olaylar.extend(atama.execute(w))
        if not w.gorev_kuyrugu and not w.aktif_gorevler:
            break

    # Tüm görevler tamam, kuyrukta hiçbir görev kalmadı
    assert w.gorev_kuyrugu == []
    assert w.aktif_gorevler == {}

    # Hiçbir robot hatada olmamalı
    for r in w.robotlar.values():
        assert (
            r.durum == RobotDurum.BOS
        ), f"{r.id} HATA_DURUYOR ya da askıda kaldı: {r.durum}"

    # En az 8 gorev_tamamlandi event'i olmalı
    tamamlandi = [e for e in olaylar if e["olay"] == "gorev_tamamlandi"]
    assert len(tamamlandi) == 8

    # Hata event'i olmamalı (deadlock_hata, robot_hata)
    hata = [
        e
        for e in olaylar
        if e["olay"] in ("deadlock_hata", "robot_hata", "rota_bulunamadi")
    ]
    assert hata == [], f"Beklenmeyen hata event'leri: {hata}"


def test_3_robot_dar_kanal_swap_recovery_yapar(real_world: World):
    """3 robot aynı koridor (y=4) üzerinde uçtan uca farklı yönlere çıkarsa,
    cooperative-light + WAIT/replan ile tıkanmasız tamamlamalı."""
    w = real_world
    # AGV-04'ü kapat (görev verme) — odak 3 robot
    w.robotlar.pop("AGV-04", None)

    # 3 robot karşılıklı geçişe zorlanır:
    w.gorev_kuyrugu.extend(
        [
            # AGV-01: sol uçtan sağ uca
            AgvGorev(
                gorev_id="g-A",
                wms_gorev_id=2001,
                wms_gorev_tipi="Yerlestirme",
                kaynak_raf_id=101,
                hedef_raf_id=107,
            ),
            # AGV-02: sağ uçtan sol uca (zıt yön)
            AgvGorev(
                gorev_id="g-B",
                wms_gorev_id=2002,
                wms_gorev_tipi="Yerlestirme",
                kaynak_raf_id=107,
                hedef_raf_id=101,
            ),
            # AGV-03: orta — alt rafa
            AgvGorev(
                gorev_id="g-C",
                wms_gorev_id=2003,
                wms_gorev_tipi="Yerlestirme",
                kaynak_raf_id=104,
                hedef_raf_id=204,
            ),
        ]
    )

    tick = TickUseCase()
    atama = GorevAtamaUseCase()
    for _ in range(800):
        tick.execute(w)
        atama.execute(w)
        if not w.gorev_kuyrugu and not w.aktif_gorevler:
            break

    assert w.gorev_kuyrugu == []
    assert w.aktif_gorevler == {}
    for r in w.robotlar.values():
        assert r.durum == RobotDurum.BOS
