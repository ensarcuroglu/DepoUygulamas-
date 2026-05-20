"""Demo/test paneli endpoint'leri.

Frontend AGV İzleme sayfasından senaryo tetiklemek içindir.
`AGV_TEST_PANEL_ENABLED=true` iken main.py tarafından mount edilir.
INTERNAL_API_KEY istemez; üretimde gateway/proxy seviyesinde kapatılması
beklenir. AgvSimService DB'ye yazmaz — kayıtlar in-memory World üzerindedir.

Not: Test endpoint'leri authoritative görev oluşturmaz; bu görevler için
WMS callback NoOp olur (`gorev_tamamlandi` event yayınlanır ama BackendProje
tarafında karşılığı yoksa orphan kalır). Bu kabul edilebilir demo davranışı.
"""

from __future__ import annotations

import random
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.entities.agv_gorev import AgvGorev
from app.core.entities.palet import Palet, PaletDurum
from app.core.entities.robot import RobotDurum
from app.core.services.rota_planlayici import rezervasyonu_birak
from app.core.services.world import World, get_world

router = APIRouter(prefix="/api/agv/test", tags=["AGV Test Paneli"])


# ── Pydantic body modelleri ──


class GorevOlusturBody(BaseModel):
    kaynak_raf_id: Optional[int] = None
    hedef_raf_id: Optional[int] = None
    palet_id: Optional[int] = None
    oncelik: int = Field(default=5, ge=1, le=5)


class YogunTrafikBody(BaseModel):
    gorev_sayisi: int = Field(default=8, ge=1, le=50)


class DusukBataryaBody(BaseModel):
    robot_id: Optional[str] = None
    seviye: float = Field(default=18.0, ge=0.0, le=100.0)


class RobotArizaBody(BaseModel):
    robot_id: Optional[str] = None


# ── Yardımcı ──


def _rastgele_raf_cifti(world: World) -> tuple[int, int]:
    raf_ids = list(world.grid.raflar.keys())
    if len(raf_ids) < 2:
        raise HTTPException(400, "Grid'de en az 2 raf olmalı")
    kaynak = random.choice(raf_ids)
    hedef = random.choice([r for r in raf_ids if r != kaynak])
    return kaynak, hedef


def _gorev_olustur(
    world: World,
    kaynak_raf_id: int,
    hedef_raf_id: int,
    palet_id: Optional[int] = None,
    oncelik: int = 5,
) -> AgvGorev:
    if kaynak_raf_id not in world.grid.raflar:
        raise HTTPException(400, f"Kaynak raf {kaynak_raf_id} grid'de yok")
    if hedef_raf_id not in world.grid.raflar:
        raise HTTPException(400, f"Hedef raf {hedef_raf_id} grid'de yok")
    if kaynak_raf_id == hedef_raf_id:
        raise HTTPException(400, "Kaynak ve hedef raf aynı")

    gorev = AgvGorev(
        gorev_id=f"test-{uuid.uuid4().hex[:8]}",
        wms_gorev_id=random.randint(900000, 999999),  # demo görev — WMS'te karşılığı yok
        wms_gorev_tipi="Yerlestirme",
        kaynak_raf_id=kaynak_raf_id,
        hedef_raf_id=hedef_raf_id,
        palet_id=palet_id,
        oncelik=oncelik,
    )
    world.gorev_kuyrugu.append(gorev)
    # Palet kaydı (router/gorevler.py ile aynı şablon)
    kaynak_raf = world.grid.raflar[kaynak_raf_id]
    palet_key = World.palet_anahtari(gorev)
    world.paletler[palet_key] = Palet(
        palet_key=palet_key,
        palet_id=palet_id,
        durum=PaletDurum.KAYNAKTA_BEKLIYOR,
        x=kaynak_raf.x,
        y=kaynak_raf.y,
        kaynak_raf_id=kaynak_raf_id,
        hedef_raf_id=hedef_raf_id,
        gorev_id=gorev.gorev_id,
    )
    return gorev


# ── Endpoint'ler ──


@router.post("/gorev")
async def test_gorev_olustur(body: GorevOlusturBody) -> dict:
    """Tek bir test görevi oluşturur — raf id'leri verilmezse rastgele seçer."""
    world = get_world()
    async with world.lock:
        kaynak = body.kaynak_raf_id
        hedef = body.hedef_raf_id
        if kaynak is None or hedef is None:
            rk, rh = _rastgele_raf_cifti(world)
            kaynak = kaynak if kaynak is not None else rk
            hedef = hedef if hedef is not None else rh
        gorev = _gorev_olustur(
            world,
            kaynak_raf_id=kaynak,
            hedef_raf_id=hedef,
            palet_id=body.palet_id,
            oncelik=body.oncelik,
        )
    return {
        "kabul_edildi": True,
        "agv_gorev_id": gorev.gorev_id,
        "kaynak_raf_id": gorev.kaynak_raf_id,
        "hedef_raf_id": gorev.hedef_raf_id,
        "kuyruk_uzunlugu": len(world.gorev_kuyrugu),
    }


@router.post("/yogun-trafik")
async def test_yogun_trafik(body: YogunTrafikBody) -> dict:
    """Birden fazla rastgele görev ekler — paralel trafik testi."""
    world = get_world()
    olusturulan: list[str] = []
    async with world.lock:
        for _ in range(body.gorev_sayisi):
            k, h = _rastgele_raf_cifti(world)
            g = _gorev_olustur(world, kaynak_raf_id=k, hedef_raf_id=h, oncelik=5)
            olusturulan.append(g.gorev_id)
    return {
        "kabul_edildi": True,
        "gorev_sayisi": len(olusturulan),
        "agv_gorev_idleri": olusturulan,
        "kuyruk_uzunlugu": len(world.gorev_kuyrugu),
    }


@router.post("/dusuk-batarya")
async def test_dusuk_batarya(body: DusukBataryaBody) -> dict:
    """Bir robotun bataryasını düşürür — otonom şarja dönüş tetiklenir."""
    world = get_world()
    async with world.lock:
        robot = (
            world.robotlar.get(body.robot_id)
            if body.robot_id
            else next(iter(world.robotlar.values()), None)
        )
        if robot is None:
            raise HTTPException(404, "Robot bulunamadı")
        robot.batarya_yuzde = body.seviye
    return {
        "robot_id": robot.id,
        "yeni_batarya": robot.batarya_yuzde,
    }


@router.post("/robot-ariza")
async def test_robot_ariza(body: RobotArizaBody) -> dict:
    """Bir robotu HATA_DURUYOR durumuna düşürür."""
    world = get_world()
    async with world.lock:
        robot = (
            world.robotlar.get(body.robot_id)
            if body.robot_id
            else next(
                (r for r in world.robotlar.values() if r.durum != RobotDurum.HATA_DURUYOR),
                None,
            )
        )
        if robot is None:
            raise HTTPException(404, "Uygun robot bulunamadı")
        robot.hata_durumuna_al()
        rezervasyonu_birak(world, robot)
    return {"robot_id": robot.id, "durum": robot.durum.value}


@router.post("/deadlock-senaryosu")
async def test_deadlock_senaryosu() -> dict:
    """Aynı koridorda zıt yönlü iki görev — kooperatif çözüm testi."""
    world = get_world()
    raf_ids = list(world.grid.raflar.keys())
    if len(raf_ids) < 2:
        raise HTTPException(400, "Grid'de en az 2 raf olmalı")
    a, b = raf_ids[0], raf_ids[-1]
    async with world.lock:
        g1 = _gorev_olustur(world, kaynak_raf_id=a, hedef_raf_id=b, oncelik=1)
        g2 = _gorev_olustur(world, kaynak_raf_id=b, hedef_raf_id=a, oncelik=1)
    return {
        "kabul_edildi": True,
        "gorev_idleri": [g1.gorev_id, g2.gorev_id],
        "kuyruk_uzunlugu": len(world.gorev_kuyrugu),
    }


@router.post("/duraklat")
async def test_duraklat() -> dict:
    world = get_world()
    async with world.lock:
        world.duraklatildi = True
    return {"duraklatildi": True}


@router.post("/devam")
async def test_devam() -> dict:
    world = get_world()
    async with world.lock:
        world.duraklatildi = False
    return {"duraklatildi": False}


@router.post("/sifirla")
async def test_sifirla() -> dict:
    """Görev kuyruğunu, aktif görevleri ve palet kayıtlarını temizler.

    Robot konumlarına dokunulmaz; HATA_DURUYOR robotlar varsa BOS'a çekilir.
    """
    world = get_world()
    async with world.lock:
        world.gorev_kuyrugu.clear()
        world.aktif_gorevler.clear()
        world.paletler.clear()
        for r in world.robotlar.values():
            if r.durum == RobotDurum.HATA_DURUYOR:
                r.sifirla()
            r.rota = None
            r.aktif_gorev_id = None
            r.bekleme_kalani = 0
            rezervasyonu_birak(world, r)
            r.sarja_donuyor = False
        world.robot_stuck.clear()
        world.robot_son_konum.clear()
    return {"sifirlandi": True}
