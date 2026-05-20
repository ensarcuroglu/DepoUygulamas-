"""World — in-memory simülasyon dünyası (process-local singleton)."""

from __future__ import annotations

import asyncio
import time
from typing import Optional

from app.core.entities.agv_gorev import AgvGorev
from app.core.entities.grid import Grid
from app.core.entities.palet import Palet, PaletDurum
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
        # Palet kayıtları — görsel runtime state (DB değil).
        # Görev kuyruğa girince eklenir, hedefe bırakıldıktan sonra orada kalır.
        self.paletler: dict[str, Palet] = {}

    def robot_ekle(self, robot: Robot) -> None:
        if robot.id in self.robotlar:
            raise ValueError(f"Robot {robot.id} zaten var")
        self.robotlar[robot.id] = robot

    def bos_robot_bul(self) -> Optional[Robot]:
        # Şarja dönen veya bataryası kritik olan robotlar görev almasın
        from app.core.services.batarya import BATARYA_KRITIK
        for r in self.robotlar.values():
            if r.durum != RobotDurum.BOS:
                continue
            if r.sarja_donuyor:
                continue
            if r.batarya_yuzde < BATARYA_KRITIK:
                continue
            return r
        return None

    def diger_robot_konumlari(self, kendisi: Robot) -> set:
        from app.core.entities.grid import Cell
        return {Cell(r.x, r.y) for r in self.robotlar.values() if r.id != kendisi.id}

    def bos_park_bul(self, robot: Robot):
        """Robot için en uygun boş bekleme hücresi.

        Önce robotun atanmış `bekleme_konumu`'nu dener; üzerinde başka robot
        yoksa onu döndürür. Aksi halde `grid.bekleme_konumlari` içinden,
        başka robotun şu an üzerinde olmadığı ve başka robotun aktif park
        hedefi olmadığı en yakın hücreyi seçer. Hiçbiri uygun değilse None.
        """
        from app.core.entities.grid import Cell

        diger_konumlar = {
            Cell(r.x, r.y) for r in self.robotlar.values() if r.id != robot.id
        }
        # Başka robotların park hedefi olarak rezerve ettikleri konumlar
        diger_park_hedefleri = {
            r.bekleme_konumu
            for r in self.robotlar.values()
            if r.id != robot.id
            and r.bekleme_konumu is not None
            and r.durum
            in (RobotDurum.BEKLEME_YERINE_DONUYOR,)
        }

        adaylar: list[Cell] = []
        if robot.bekleme_konumu is not None:
            adaylar.append(robot.bekleme_konumu)
        adaylar.extend(self.grid.bekleme_konumlari)

        gorulen: set[Cell] = set()
        for c in adaylar:
            if c in gorulen:
                continue
            gorulen.add(c)
            if c in diger_konumlar:
                continue
            if c in diger_park_hedefleri:
                continue
            if not self.grid.gecilebilir_mi(c):
                continue
            return c
        return None

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
                "batarya": round(r.batarya_yuzde, 1),
                "sarja_donuyor": r.sarja_donuyor,
                "bekleme_konumu": (
                    [r.bekleme_konumu.x, r.bekleme_konumu.y]
                    if r.bekleme_konumu is not None
                    else None
                ),
            }
            for r in self.robotlar.values()
        ]

    @staticmethod
    def palet_anahtari(gorev: AgvGorev) -> str:
        """Görevden palet için stabil anahtar üretir (palet_id varsa onu kullan)."""
        if gorev.palet_id is not None:
            return f"palet:{gorev.palet_id}"
        return f"gorev:{gorev.gorev_id}"

    def palet_listesi(self) -> list[dict]:
        """WS payload için palet özetleri.

        ROBOT_UZERINDE palet için x/y robotun anlık konumuyla doldurulur ki
        frontend her tick'te doğru konumu görsün (lerp kendisi yapar).
        """
        sonuc: list[dict] = []
        for p in self.paletler.values():
            x, y = p.x, p.y
            if p.durum == PaletDurum.ROBOT_UZERINDE and p.robot_id is not None:
                r = self.robotlar.get(p.robot_id)
                if r is not None:
                    x, y = r.x, r.y
            sonuc.append(
                {
                    "palet_key": p.palet_key,
                    "palet_id": p.palet_id,
                    "durum": p.durum.value,
                    "x": x,
                    "y": y,
                    "kaynak_raf_id": p.kaynak_raf_id,
                    "hedef_raf_id": p.hedef_raf_id,
                    "robot_id": p.robot_id,
                    "gorev_id": p.gorev_id,
                }
            )
        return sonuc

    def aktif_gorev_listesi(self) -> list[dict]:
        """WS delta için özet — frontend görev paneli kullanır."""
        # robot_id'yi bulmak için ters arama
        gorev_to_robot: dict[str, str] = {}
        for r in self.robotlar.values():
            if r.aktif_gorev_id:
                gorev_to_robot[r.aktif_gorev_id] = r.id
        return [
            {
                "gorev_id": g.gorev_id,
                "wms_gorev_id": g.wms_gorev_id,
                "wms_gorev_tipi": g.wms_gorev_tipi,
                "kaynak_raf_id": g.kaynak_raf_id,
                "hedef_raf_id": g.hedef_raf_id,
                "robot_id": gorev_to_robot.get(g.gorev_id),
                "baslama_tick": g.baslama_tick,
            }
            for g in self.aktif_gorevler.values()
        ]

    def snapshot_tam(self) -> dict:
        """WS bağlantısının ilk mesajı — grid + tüm robotlar."""
        from app.core.entities.grid import CellTipi
        engeller: list[dict[str, int]] = []
        for y, satir in enumerate(self.grid.hucreler):
            for x, tip in enumerate(satir):
                if tip == CellTipi.ENGEL:
                    engeller.append({"x": x, "y": y})
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
                "bekleme_konumlari": [
                    {"x": c.x, "y": c.y} for c in self.grid.bekleme_konumlari
                ],
                "engeller": engeller,
            },
            "robotlar": self.robot_dict_listesi(),
            "paletler": self.palet_listesi(),
        }

    def snapshot_delta(self) -> dict:
        """Her tick'te WS'e gönderilen delta — sadece dinamik state."""
        return {
            "tick_no": self.tick_no,
            "ts": time.time(),
            "robotlar": self.robot_dict_listesi(),
            "kuyruk_uzunlugu": len(self.gorev_kuyrugu),
            "aktif_gorev_sayisi": len(self.aktif_gorevler),
            "aktif_gorevler": self.aktif_gorev_listesi(),
            "paletler": self.palet_listesi(),
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
