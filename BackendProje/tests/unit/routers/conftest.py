"""Unit router testleri için ortak fixture'lar.

FastAPI app'ini doğrudan TestClient ile sarar; `get_current_user` ve
DI container fonksiyonları `app.dependency_overrides` ile mock'lanır.
DB bağlantısı gerekmez — use-case / service mock'lar davranışı sağlar.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token, get_current_user
from database import get_db
from limiter import limiter
from main import app


def _fake_user(rol: str, *, id: int = 1, depo_id: int | None = 7, kullanici_adi: str | None = None):
    """Router kodunun beklediği kullanıcı attribute'larını taşıyan stub.

    `kullanici_to_entity` ORM'den okunan tüm alanları talep ediyor; None olanları
    doldurarak mapper'ı mock'lamadan çalıştırabiliyoruz.
    """
    from datetime import datetime

    return SimpleNamespace(
        id=id,
        kullanici_adi=kullanici_adi or f"test_{rol}",
        sifre_hash="$fake$hash",
        ad_soyad=f"Test {rol}",
        rol=rol,
        telefon=None,
        email=None,
        departman=None,
        sicil_no=None,
        kart_numarasi=None,
        depo_id=depo_id,
        depo_erisimi_yok=False,
        refresh_token_hash=None,
        refresh_token_son_kullanim=None,
        olusturma_tarihi=datetime(2026, 1, 1),
    )


@pytest.fixture
def _fake_db():
    """Router'ların `db: Session = Depends(get_db)` beklediği stub."""
    return SimpleNamespace(commit=lambda: None, rollback=lambda: None, query=lambda *a, **k: None)


@pytest.fixture
def override_user():
    """Her test override'ı yönetebilsin diye yardımcı callable döner."""
    users = {}

    def _set(user):
        users["u"] = user
        app.dependency_overrides[get_current_user] = lambda: users["u"]
        return user

    limiter.reset()
    yield _set
    app.dependency_overrides.clear()
    limiter.reset()


@pytest.fixture
def admin_user(override_user):
    return override_user(_fake_user("admin", id=1, depo_id=7, kullanici_adi="admin_t"))


@pytest.fixture
def depocu_user(override_user):
    return override_user(_fake_user("depocu", id=2, depo_id=7, kullanici_adi="depocu_t"))


@pytest.fixture
def lojistik_user(override_user):
    return override_user(_fake_user("lojistik", id=3, depo_id=None, kullanici_adi="lojistik_t"))


@pytest.fixture
def client(_fake_db):
    """TestClient — DB dependency'si de mock'lanmış."""
    app.dependency_overrides[get_db] = lambda: _fake_db
    with TestClient(app) as c:
        yield c
    # get_current_user override'ı override_user fixture'ında temizleniyor


@pytest.fixture
def anon_client():
    """Geçerli token fabrikalaması olmadan çağrılacak client (401 senaryoları)."""
    limiter.reset()
    with TestClient(app) as c:
        yield c
    limiter.reset()


@pytest.fixture
def anon_token():
    """get_current_user'ı bypass etmeden gerçek token üretimi — db'siz senaryolarda kullanılmaz."""
    return create_access_token(data={"sub": "nonexistent_user"})
