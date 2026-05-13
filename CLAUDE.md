# CLAUDE.md

AI coding agent için operasyonel referans. Detaylı dokümanlar `docs/agent/` altında.

## Project Summary

**Depo Yönetim Sistemi (WMS)** — Lot/palet takibi, putaway/pick görev akışları, üretim paleti kabul, mobil terminal PWA ve operatör performans (LMS) modülü içeren full-stack uygulama. FastAPI backend (Clean Architecture) + React/Vite frontend + Docker Compose dev stack + MySQL + üç bağımsız mikroservis (WmsAiService, DocAiService, AgvSimService).

## Main Directories

- `BackendProje/` — FastAPI backend (Clean Architecture: api → application → core / infrastructure).
- `ReactProje/` — React 19 + Vite 7 frontend (PWA, TanStack Query). TypeScript yok.
- `WmsAiService/` — LangChain + Ollama doğal dil → SQL servisi (read-only view'lar) + doküman RAG asistanı (Chroma; ingestion'da LlamaIndex `MarkdownNodeParser`).
- `DocAiService/` — Belge AI mikroservisi (text PDF + VLM); irsaliye taslağı çıkarır, DB yazmaz.
- `AgvSimService/` — AGV/AMR simülasyonu (in-memory world, asyncio tick loop, A*/CA*).
- `backend-worker` (compose servisi) — `python -m app.infrastructure.messaging.operator_performans_consumer`; `RABBITMQ_ENABLED=true` iken LMS event'lerini queue'dan tüketir. `false` iken boş döngüde bekler.

## Common Commands

### Docker Compose (önerilen dev giriş)

```bash
docker compose up -d                    # baslat
docker compose up --build               # ilk kurulum / dependency degisikligi
docker compose ps
docker compose logs -f backend
docker compose down                     # durdur
docker compose down -v --remove-orphans # temiz DB icin
```

### Backend (`BackendProje/`)

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
ruff check .
pytest                  # tum testler (test DB: depo_db_test)
pytest -m unit
alembic upgrade head
alembic revision --autogenerate -m "aciklama"
python seed.py
```

### Frontend (`ReactProje/`)

```bash
npm install
npm run dev
npm run lint
npm run build
```

### WmsAiService

```bash
cd WmsAiService && uvicorn main:app --reload --host 127.0.0.1 --port 8001
```

### DocAiService

```bash
cd DocAiService
uvicorn main:app --reload --host 127.0.0.1 --port 8003
pytest
curl -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8003/healthz
```

### AgvSimService

```bash
cd AgvSimService
uvicorn main:app --reload --host 127.0.0.1 --port 8002
pytest
```

### RabbitMQ (LMS event hatti)

```bash
# Servis ayaga kaldir (compose icinden)
docker compose up -d rabbitmq backend backend-worker

# Mode degistir
# infra/env/dev.env veya BackendProje/.env icinde:
#   RABBITMQ_ENABLED=true   -> relay + consumer aktif
#   RABBITMQ_ENABLED=false  -> eski 5dk APScheduler aggregator

# Queue / exchange inceleme
docker compose exec rabbitmq rabbitmqctl list_queues name messages
docker compose exec rabbitmq rabbitmqctl list_exchanges name type durable

# DLQ temizle
docker compose exec rabbitmq rabbitmqctl purge_queue depo.lms.operator_metrikleri.dlq

# Broker gerektiren testler (opsiyonel)
cd BackendProje && pytest -m rabbitmq
```

## Development Rules

- Değişiklik yapmadan önce ilgili dosyaları oku.
- Gereksiz yeni dosya oluşturma; tercihen mevcut dosyaları düzenle.
- Değişiklikleri dar tut; alakasız refactor yapma.
- Backend tarafında Clean Architecture katman sınırlarını koru: `core → application → infrastructure → api` (iç katman dışı import etmez).
- Router → use case → repository zincirini tercih et; DI factory'lerini `app/infrastructure/di/modules/` altına ekle ve `container.py`'den re-export et.
- ORM model değişti → Alembic migration oluştur **ve** `alembic upgrade head` ile uygula. Migration yazmak yeterli değildir.
- Yerleştirme/toplama görev geçişi eklenirken LMS `IPerformansEventPublisher` hook'unu çağırmayı unutma; aksi halde outbox akışı kırılır.
- Frontend TypeScript kullanmaz; `.js` / `.jsx` yapısına bağlı kal.
- React Query mevcut `queryKeys.js` pattern'ine uy.
- İsimlendirme Türkçe (snake_case fonksiyon, PascalCase sınıf/entity).
- DocAiService DB'ye yazmaz; BackendProje authoritative kalır. `INTERNAL_API_KEY` / `X-Internal-Api-Key` / `Idempotency-Key` sözleşmesini bozma.
- AgvSimService tek süreç çalışır; asla replica / multiple worker. `World` in-memory singleton'dır.
- Docker Compose çalışırken aynı servisleri ayrıca `uvicorn` ile başlatma — port çakışır.
- Backend değişikliği sonrası `ruff check .` + `pytest -m unit`; frontend sonrası `npm run lint`.

## Important Notes

- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/docs`
- Backend port: **8000**
- WmsAiService port: **8001**
- AgvSimService port: **8002**
- DocAiService port: **8003**
- RabbitMQ AMQP: **5672** / Management UI: `http://localhost:15672` (`guest`/`guest`)
- Docker Compose project name: `depo-dev`
- Proje yolu ASCII olmalı: `D:\Ensar Dosya\DepoUygulamasi`
- Varsayılan VLM model (DocAi): `qwen3-vl:4b`
- Varsayılan WMS AI model: `qwen2.5-coder:7b`
- `RABBITMQ_ENABLED=false` default — LMS event'leri için eski APScheduler 5dk polling aggregator çalışır. `true` yapıldığında relay + consumer worker akışı devreye girer; bkz. `docs/agent/rabbitmq-operations.md`.

## Do Not Touch

- `ReactProje/dist/`, `ReactProje/dev-dist/`, `ReactProje/stats.html` (build çıktıları)
- `__pycache__/`, `.venv/`, `venv/`, `.coverage`
- `BackendProje/alembic/versions/` — sadece Alembic ile oluştur, elle düzenleme.
- `WmsAiService/wms_chroma_db/` — ChromaDB persistent store (generated).
- Standalone `migrate_*.py` scriptleri idempotent değil; tekrar çalıştırma.

## More Detailed Documentation

- Mimari detayları: `docs/agent/project-architecture.md`
- Docker detayları: `docs/agent/docker-compose.md`
- Backend detayları: `docs/agent/backend-notes.md`
- Frontend detayları: `docs/agent/frontend-notes.md`
- AI servis detayları: `docs/agent/ai-services.md`
- Ortam değişkenleri: `docs/agent/env-reference.md`
- RabbitMQ operasyon ve runbook: `docs/agent/rabbitmq-operations.md`
