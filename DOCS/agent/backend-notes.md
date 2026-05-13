# Backend Notes (BackendProje/)

FastAPI + Clean Architecture. Klasör yapısı ve mimari detayı için `project-architecture.md` dosyasına bak.

## Komutlar

```bash
cd BackendProje

# Dependency
pip install -r requirements.txt
pip install -r requirements-test.txt

# Dev server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Lint
ruff check .

# Type check (pyright basic, sadece app/)
pyright

# Testler (test DB: depo_db_test)
pytest
pytest -m unit
pytest -m integration
pytest -m api
pytest -m concurrency
pytest tests/unit/test_feature_flags.py
pytest -k "test_token_rotation"

# Coverage
pytest --cov=app --cov-report=term --disable-warnings -q --tb=short

# Seed (admin + depocu)
python seed.py

# Alembic
alembic upgrade head
alembic revision --autogenerate -m "migration_aciklamasi"
```

## Kurallar

- Yeni iş akışları router → use case → repository zinciriyle yazılır; `auth`, idempotency ve bazı stok/terminal endpoint'leri sınırlı doğrudan `Session` kullanır.
- DI: `app/infrastructure/di/modules/<domain>.py` factory → `container.py` re-export.
- Repository abstract `app/core/repositories/` ↔ concrete `app/infrastructure/persistence/repositories/`.
- Domain entity'ler `app/core/entities/` dataclass.
- Exception zinciri: domain exception → `APIException` → merkezi handler.
- Auth: `get_current_user`, `require_role("admin")`.
- Loglama: `SistemLog` kritik CRUD'larda router'dan.

## Migration Notları

- Resmi araç Alembic; ayrıca elle çalıştırılan `migrate_*.py` scriptleri var (idempotent değil).
- `models.py` değişti → migration zorunlu.
- Her ortamda `alembic upgrade head` koşturulmalı.
- `main.py` lifespan'inde `_migration_drift_kontrol`; prod'da `DEPO_STRICT_MIGRATION=1` ile drift'te boot durur. `DEPO_SKIP_MIGRATION_CHECK=1` acil durum atlama.

## Test Altyapısı

- `tests/conftest.py` merkezi fixture (engine, db_session, client, auth).
- `tests/factories/` factory-boy.
- `tests/unit/`, `tests/integration/` (concurrency, idempotency, putaway E2E), `tests/api/routers/`.
- Test DB adı `depo_db_test` zorunlu (`test` ifadesi içermezse güvenlik kontrolü hata verir).

## Operatör Performans (LMS)

LMS detayları `project-architecture.md` içinde. Özetle: outbox + APScheduler aggregator + UPH. Yerleştirme/toplama görev geçişlerinde `IPerformansEventPublisher` çağrısı atlanırsa outbox akışı kırılır.
