"""Faz 0 smoke test — uygulama ayağa kalkıyor mu?"""

from fastapi.testclient import TestClient

from main import app


def test_healthz_dondurur_ok():
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "AgvSimService"
    assert "tick_hz" in body
