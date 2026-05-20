"""POST /api/agv/test/* — demo/test paneli endpoint testleri."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _sifirla(client):
    r = client.post("/api/agv/test/sifirla")
    assert r.status_code == 200


def test_tek_gorev_olusturma_rastgele(client):
    _sifirla(client)
    r = client.post("/api/agv/test/gorev", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["kabul_edildi"] is True
    assert body["kuyruk_uzunlugu"] >= 1
    assert body["agv_gorev_id"].startswith("test-")


def test_tek_gorev_olusturma_belirli_raflar(client):
    _sifirla(client)
    r = client.post(
        "/api/agv/test/gorev",
        json={"kaynak_raf_id": 101, "hedef_raf_id": 201, "palet_id": 7},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["kaynak_raf_id"] == 101
    assert body["hedef_raf_id"] == 201


def test_gorev_olusturma_ayni_raf_400(client):
    r = client.post(
        "/api/agv/test/gorev",
        json={"kaynak_raf_id": 101, "hedef_raf_id": 101},
    )
    assert r.status_code == 400


def test_yogun_trafik_n_gorev_ekler(client):
    _sifirla(client)
    r = client.post("/api/agv/test/yogun-trafik", json={"gorev_sayisi": 5})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["gorev_sayisi"] == 5
    assert body["kuyruk_uzunlugu"] >= 5


def test_dusuk_batarya_robotu_etkiler(client):
    r = client.post("/api/agv/test/dusuk-batarya", json={"seviye": 15.0})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["yeni_batarya"] == 15.0


def test_robot_ariza_hata_duruyora_alir(client):
    _sifirla(client)
    r = client.post("/api/agv/test/robot-ariza", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["durum"] == "HataDuruyor"


def test_deadlock_senaryosu_iki_zit_gorev_ekler(client):
    _sifirla(client)
    r = client.post("/api/agv/test/deadlock-senaryosu", json={})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["gorev_idleri"]) == 2


def test_duraklat_ve_devam(client):
    r = client.post("/api/agv/test/duraklat")
    assert r.status_code == 200
    assert r.json()["duraklatildi"] is True
    r = client.post("/api/agv/test/devam")
    assert r.status_code == 200
    assert r.json()["duraklatildi"] is False


def test_sifirla_palet_ve_gorev_temizler(client):
    client.post("/api/agv/test/yogun-trafik", json={"gorev_sayisi": 3})
    r = client.post("/api/agv/test/sifirla")
    assert r.status_code == 200
    # Bir sonraki snapshot kuyruğun temizlendiğini göstermeli
    g = client.get("/api/agv/grid")
    assert g.status_code == 200
