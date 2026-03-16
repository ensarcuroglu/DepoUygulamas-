# Backend Test Altyapısı Tasarımı

> Tarih: 2026-03-16
> Durum: Onaylandı — implementasyon bekliyor

---

## 1. Amaç

Depo Yönetim Sistemi backend'i için tam kapsamlı test altyapısı kurmak. Entity'den API endpoint'e kadar her katman test edilecek.

## 2. Kapsam

- **Dahil:** Backend (FastAPI) — unit, integration, API testleri
- **Hariç:** Frontend (React), Docker-based ortam, load/performance testing, coverage eşik zorunluluğu

## 3. Teknolojiler

| Paket | Versiyon | Amaç |
|-------|----------|------|
| pytest | >=8.0 | Test runner |
| pytest-asyncio | >=0.23 | Async endpoint desteği |
| httpx | >=0.27 | FastAPI TestClient (ASGITransport) |
| pytest-cov | >=5.0 | Coverage raporlama |
| factory-boy | >=3.3 | Test verisi üretimi (SQLAlchemy entegrasyonu) |

## 4. Veritabanı Stratejisi

- **Gerçek MySQL** — ayrı `depo_db_test` veritabanı
- **Temizlik:** Her test fonksiyonu öncesi tüm tabloları truncate (`FOREIGN_KEY_CHECKS=0`)
- **Engine:** `scope="session"` (tek bağlantı), **Session:** `scope="function"` (her test izole)

## 5. Dizin Yapısı

```
BackendProje/
├── requirements-test.txt
├── pytest.ini
├── .env.test
└── tests/
    ├── conftest.py
    ├── factories/
    │   ├── __init__.py
    │   ├── kullanici_factory.py
    │   ├── urun_factory.py
    │   ├── depo_factory.py
    │   └── ...
    ├── unit/
    │   ├── entities/
    │   └── use_cases/
    ├── integration/
    │   ├── repositories/
    │   └── crud/
    └── api/
        └── routers/
```

## 6. conftest.py Tasarımı

### Engine & Session

```python
@pytest.fixture(scope="session")
def engine():
    load_dotenv(".env.test")
    engine = create_engine(test_db_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(engine):
    # TRUNCATE tüm tablolar (FK check kapalı)
    session = SessionLocal(bind=engine)
    yield session
    session.close()
```

### Test Client & Auth

```python
@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(client, db_session):
    # Admin oluştur → login → token al → header set et
    ...

@pytest.fixture
def depocu_client(client, db_session):
    # Depocu oluştur → login → token al → header set et
    ...
```

### Factory Bağlama

```python
@pytest.fixture(autouse=True)
def _bind_factories(db_session):
    UrunFactory._meta.sqlalchemy_session = db_session
    KullaniciFactory._meta.sqlalchemy_session = db_session
    # ... diğerleri
```

## 7. Pytest Konfigürasyonu

```ini
[pytest]
testpaths = tests
asyncio_mode = auto
markers =
    unit: Unit testler (DB gerektirmez)
    integration: Integration testler (gerçek DB)
    api: API endpoint testleri (gerçek DB + HTTP)
```

Seçici çalıştırma:
- `pytest -m unit` — hızlı, DB'siz
- `pytest -m integration` — repository/CRUD testleri
- `pytest -m api` — endpoint testleri
- `pytest` — tamamı

## 8. Test Katmanları

### Unit (`tests/unit/`)
- **Entity testleri:** Pydantic validation, iş kuralları, computed field'lar
- **Use case testleri:** Repository mock'lanır, sadece iş mantığı test edilir
- DB'ye dokunmaz, en hızlı katman

### Integration (`tests/integration/`)
- **Repository testleri:** Gerçek MySQL'e yazıp okuma
- **CRUD testleri:** Legacy CRUD fonksiyonlarının doğruluğu
- Factory ile veri oluşturulur, gerçek DB sorgulanır

### API (`tests/api/`)
- **Router testleri:** Tam HTTP döngüsü
- Auth (401), role control (403), validation (422), happy path (200)
- `admin_client`, `depocu_client` fixture'ları ile rol bazlı test

## 9. Factory Tasarımı

```python
class UrunFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Urun
        sqlalchemy_session = None  # conftest inject eder

    ad = factory.Sequence(lambda n: f"Test Ürün {n}")
    barkod = factory.Sequence(lambda n: f"BARKOD{n:06d}")
    birim = "adet"
    min_stok = 10

class LotFactory(SQLAlchemyModelFactory):
    urun = factory.SubFactory(UrunFactory)
    depo = factory.SubFactory(DepoFactory)
    lot_no = factory.Sequence(lambda n: f"LOT-{n:04d}")
```

FK zincirleri `SubFactory` ile otomatik çözülür.

## 10. GitHub Actions CI

```yaml
name: Backend Tests
on:
  push:
    branches: [main]
    paths: ['BackendProje/**']
  pull_request:
    branches: [main]
    paths: ['BackendProje/**']

services:
  mysql:
    image: mysql:8.0
    env:
      MYSQL_ROOT_PASSWORD: testpass
      MYSQL_DATABASE: depo_db_test
    ports: [3306:3306]
    options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=5

steps:
  - uses: actions/checkout@v4
  - uses: actions/setup-python@v5
    with: { python-version: '3.11' }
  - run: pip install -r BackendProje/requirements.txt -r BackendProje/requirements-test.txt
  - name: Run tests
    working-directory: BackendProje
    env:
      DB_USER: root
      DB_PASSWORD: testpass
      DB_HOST: 127.0.0.1
      DB_PORT: 3306
      DB_NAME: depo_db_test
      JWT_SECRET_KEY: ci-test-secret
    run: pytest --cov=. --cov-report=term-missing -v
```

## 11. Karar Logu

| # | Karar | Alternatifler | Neden |
|---|-------|---------------|-------|
| 1 | Sadece backend testleri | Frontend dahil | Kullanıcı tercihi |
| 2 | Tam kapsamlı katman testi | Sadece API / sadece unit | Her katmanı güvence altına alma |
| 3 | Gerçek MySQL (ayrı test DB) | SQLite in-memory / Docker | MySQL davranışları test edilsin |
| 4 | Her test öncesi truncate | Transaction rollback | Daha güvenli izolasyon |
| 5 | Coverage rapor, eşik yok | Zorunlu eşik | Görünürlük, hız kısıtlaması yok |
| 6 | GitHub Actions CI | Sadece lokal | Otomatik çalışsın |
| 7 | Katmanlı dizin yapısı | Flat / domain-based | Hibrit mimariye uygun, ölçeklenebilir |
| 8 | factory-boy | Manuel seed | FK zincirleri otomatik |
| 9 | pytest marker'ları | Sadece dizin ayrımı | Seçici çalıştırma |
| 10 | Max ~5 dk test süresi | 1-2 dk / sınırsız | Kapsamlı testlere alan, CI'da kabul edilebilir |

## 12. Performans Beklentisi

- Tam suite: max ~5 dakika
- Unit testler: <30 saniye
- `pytest -m unit` ile hızlı feedback döngüsü
