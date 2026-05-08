"""Deadlock tespit + replan + HATA_DURUYOR escalation testleri (Faz 4)."""

from __future__ import annotations

import pytest

from app.application.use_cases.gorev_atama import GorevAtamaUseCase
from app.application.use_cases.tick import (
    DEADLOCK_HATA_ESIK,
    DEADLOCK_REPLAN_ESIK,
    TickUseCase,
)
from app.core.entities.agv_gorev import AgvGorev
from app.core.entities.grid import Cell, CellTipi, Grid, RafKonumu
from app.core.entities.robot import Robot, RobotDurum
from app.core.services.world import World


@pytest.fixture
def tek_satir_world() -> World:
    """1 satır, 6 sütun: (0..5, 0). Raf (3,0)'da, yaklaşma (4,0).
    Üst/alt satır yok → swap imkânsız → deadlock zorlanabilir."""
    g = Grid(
        genislik=6,
        yukseklik=1,
        hucreler=[[CellTipi.BOS] * 6],
        raflar={
            201: RafKonumu(raf_id=201, x=5, y=0, yaklasma_x=4, yaklasma_y=0, kod="X"),
        },
    )
    # Aslında raf (3,0) yapacağız ki yaklaşmadan ulaşılsın — önce hücreyi RAF
    # yap, sonra raflara koy. Ama tek satırda raf koymak yolu kapatır; o yüzden
    # raf (5,0)'da (sağ uç), yaklaşma (4,0).
    g.hucreler[0][5] = CellTipi.RAF

    w = World(grid=g)
    return w


def test_deadlock_kafa_kafaya_replan_ya_da_hata_uretir(tek_satir_world: World):
    """İki robot tek satırda zıt yöne — biri ilerleyemez, deadlock recovery
    kanat olarak ya replan ya da HATA_DURUYOR event'i emit etmeli."""
    w = tek_satir_world
    # R1 (0,0) — soldan
    w.robot_ekle(Robot(id="AGV-01", x=0, y=0))
    # R2 (4,0) — yaklaşma noktasında durur (boş robot — atanmaz çünkü görev verilmiyor)
    w.robot_ekle(Robot(id="AGV-02", x=4, y=0))

    # R1 için görev: kaynak ve hedef aynı raf (sahte) — biz sadece KAYNAGA_GIDIYOR
    # akışını test ediyoruz, R2 kalıcı engel rolünde.
    # Görev (kaynak=201 yaklaşma (4,0), hedef=201 yaklaşma) — atama use case
    # aynı raf hata vermez (yalnızca task acceptor kontrol ediyor); manuel ekle.
    gorev = AgvGorev(
        gorev_id="g-stuck",
        wms_gorev_id=1,
        wms_gorev_tipi="Yerlestirme",
        kaynak_raf_id=201,
        hedef_raf_id=201,
    )
    w.gorev_kuyrugu.append(gorev)

    tick = TickUseCase()
    atama = GorevAtamaUseCase()
    olaylar: list[dict] = []

    # AGV-01 R2 kalıcı engelken (4,0)'a varmaya çalışır → CA* WAIT'e takılır →
    # tek satırda alternatif yok → ya rota_bulunamadi ya da tıkanma + deadlock.
    for _ in range(DEADLOCK_HATA_ESIK + 5):
        olaylar.extend(tick.execute(w))
        olaylar.extend(atama.execute(w))

    olay_tipleri = {e["olay"] for e in olaylar}
    # Recovery yollarından biri tetiklenmeli (CA* atama anında zaten None
    # dönerse `atama_basarisiz_rota_yok`; tasimaya geçişte fail ederse
    # `rota_bulunamadi`; hareket sırasında stuck → deadlock_*)
    assert (
        "atama_basarisiz_rota_yok" in olay_tipleri
        or "deadlock_replan_basarisiz" in olay_tipleri
        or "deadlock_hata" in olay_tipleri
        or "rota_bulunamadi" in olay_tipleri
    ), f"deadlock recovery event'i bekleniyordu, gelen: {olay_tipleri}"


def test_deadlock_replan_esik_dogru(tek_satir_world: World):
    """Sabit eşiklerin tutarlılığını koru (regresyon koruması)."""
    assert DEADLOCK_REPLAN_ESIK < DEADLOCK_HATA_ESIK
    assert DEADLOCK_REPLAN_ESIK >= 1
    assert DEADLOCK_HATA_ESIK >= 8  # operatör müdahalesi anlamlı olsun


def test_robot_bos_olunca_stuck_sayaci_sifirlanir(tek_satir_world: World):
    """Robot BOS'a düşünce stuck sayacı temizlenmeli."""
    w = tek_satir_world
    w.robot_ekle(Robot(id="AGV-01", x=0, y=0))
    w.robot_stuck["AGV-01"] = 5

    TickUseCase().execute(w)
    # BOS robot için _deadlock_kontrol stuck'ı temizler
    assert w.robot_stuck.get("AGV-01") is None or w.robot_stuck["AGV-01"] == 0


def test_rezervasyon_temizlenmesi_gorev_tamamlandiginda(basit_grid: Grid):
    """Görev tamamlanınca robotun rezervasyonları kalmasın."""
    w = World(grid=basit_grid)
    w.robot_ekle(Robot(id="AGV-01", x=0, y=4))
    w.gorev_kuyrugu.append(
        AgvGorev(
            gorev_id="g-1",
            wms_gorev_id=10,
            wms_gorev_tipi="Yerlestirme",
            kaynak_raf_id=101,
            hedef_raf_id=102,
        )
    )

    tick = TickUseCase()
    atama = GorevAtamaUseCase()
    for _ in range(30):
        tick.execute(w)
        atama.execute(w)

    robot = w.robotlar["AGV-01"]
    assert robot.durum == RobotDurum.BOS
    # Görev tamam → rezervasyon temizlenmeli
    assert w.reservation_table._owner_paths.get("AGV-01") in (None, [])
