"""
Merkezi Test Altyapısı
- DB engine & session yönetimi
- Truncate ile test izolasyonu
- TestClient & auth fixture'ları
"""

import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Test ortam değişkenlerini yükle (ana .env'den önce)
_env_test_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env.test")
os.environ["DEPO_APP_ENV_FILE"] = _env_test_path

from app.core.config import get_settings # noqa: E402
from database import Base, get_db # noqa: E402
from app.core.auth import create_access_token # noqa: E402
from limiter import limiter # noqa: E402
from main import app # noqa: E402

# Bcrypt hash'i bir kez hesapla — test başına ~400ms tasarruf
TEST_PASSWORD = "Test1234"
_CACHED_PASSWORD_HASH: str | None = None


def get_test_password_hash() -> str:
    global _CACHED_PASSWORD_HASH
    if _CACHED_PASSWORD_HASH is None:
        from app.core.auth import get_password_hash
        _CACHED_PASSWORD_HASH = get_password_hash(TEST_PASSWORD)
    return _CACHED_PASSWORD_HASH


# ========================
# DATABASE ENGINE (session scope)
# ========================

@pytest.fixture(scope="session")
def engine():
    """Test DB'ye bağlanan engine — tüm test session boyunca tek instance."""
    settings = get_settings(_env_test_path)
    db_name = settings.db_name
    db_url = settings.sqlalchemy_database_url
    if not db_name or "test" not in db_name.lower():
        raise RuntimeError(
            f"Güvenlik nedeniyle test olmayan veritabanı üzerinde çalışılamaz: {db_name!r}"
        )
    eng = create_engine(db_url, pool_pre_ping=True)
    # create_all mevcut tabloları migrate etmez; test DB'yi güncel metadata ile yeniden kur.
    Base.metadata.drop_all(bind=eng)
    Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


# ========================
# DB SESSION (function scope) + TRUNCATE
# ========================

@pytest.fixture(scope="function")
def db_session(engine):
    """Her test için temiz session. Test öncesi tüm tablolar truncate edilir."""
    Session = sessionmaker(bind=engine)
    session = Session()

    # FK check kapatıp truncate et — metadata'dan türetilmiş sıra
    session.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
    for table in reversed(Base.metadata.sorted_tables):
        session.execute(text(f"TRUNCATE TABLE `{table.name}`"))
    session.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    session.commit()

    yield session

    session.close()


# ========================
# TEST CLIENT
# ========================

@pytest.fixture
def client(db_session):
    """FastAPI TestClient — DB dependency override ile."""

    def _override_get_db():
        yield db_session

    limiter.reset()
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    limiter.reset()


# ========================
# AUTH FIXTURES
# ========================

@pytest.fixture
def admin_user(db_session):
    """Admin kullanıcı ve token."""
    from tests.factories import KullaniciFactory
    user = KullaniciFactory.create(
        kullanici_adi="test_admin",
        ad_soyad="Test Admin",
        rol="admin",
    )
    token = create_access_token(data={"sub": user.kullanici_adi})
    return user, token


@pytest.fixture
def depocu_user(db_session):
    """Depocu kullanıcı ve token."""
    from tests.factories import KullaniciFactory, DepoFactory
    depo = DepoFactory.create()
    user = KullaniciFactory.create(
        kullanici_adi="test_depocu",
        ad_soyad="Test Depocu",
        rol="depocu",
        depo_id=depo.id,
    )
    token = create_access_token(data={"sub": user.kullanici_adi})
    return user, token


@pytest.fixture
def admin_client(client, admin_user):
    """Authorization header'ı set edilmiş admin client."""
    _, token = admin_user
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def depocu_client(client, depocu_user):
    """Authorization header'ı set edilmiş depocu client."""
    _, token = depocu_user
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest.fixture
def lojistik_user(db_session):
    """Lojistik kullanıcı ve token."""
    from tests.factories import KullaniciFactory
    user = KullaniciFactory.create(
        kullanici_adi="test_lojistik",
        ad_soyad="Test Lojistik",
        rol="lojistik",
    )
    token = create_access_token(data={"sub": user.kullanici_adi})
    return user, token


@pytest.fixture
def lojistik_client(client, lojistik_user):
    """Authorization header'ı set edilmiş lojistik client."""
    _, token = lojistik_user
    client.headers["Authorization"] = f"Bearer {token}"
    return client
