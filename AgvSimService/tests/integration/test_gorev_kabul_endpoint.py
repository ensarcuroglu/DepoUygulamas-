"""POST /api/agv/gorevler — entegrasyon testi (lifespan + grid yüklenir)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_healthz_lifespan_sonrasi_calisir(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "AgvSimService"


def test_grid_endpoint_raflari_dondurur(client):
    r = client.get("/api/agv/grid")
    assert r.status_code == 200
    grid = r.json()["grid"]
    assert grid["genislik"] > 0 and grid["yukseklik"] > 0
    assert len(grid["raflar"]) >= 2


def test_gorev_kabul_basarili(client):
    r = client.post(
        "/api/agv/gorevler",
        json={
            "wms_gorev_id": 42,
            "wms_gorev_tipi": "Yerlestirme",
            "kaynak_raf_id": 101,
            "hedef_raf_id": 201,
            "palet_id": 990,
            "oncelik": 5,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["kabul_edildi"] is True
    assert body["agv_gorev_id"].startswith("agv-")


def test_gorev_kabul_olmayan_raf_400(client):
    r = client.post(
        "/api/agv/gorevler",
        json={
            "wms_gorev_id": 99,
            "wms_gorev_tipi": "Yerlestirme",
            "kaynak_raf_id": 999,
            "hedef_raf_id": 101,
        },
    )
    assert r.status_code == 400


def test_gorev_kabul_ayni_raf_400(client):
    r = client.post(
        "/api/agv/gorevler",
        json={
            "wms_gorev_id": 100,
            "wms_gorev_tipi": "Yerlestirme",
            "kaynak_raf_id": 101,
            "hedef_raf_id": 101,
        },
    )
    assert r.status_code == 400


def test_robotlar_snapshot(client):
    r = client.get("/api/agv/robotlar")
    assert r.status_code == 200
    body = r.json()
    assert "tick_no" in body
    assert isinstance(body["robotlar"], list)
