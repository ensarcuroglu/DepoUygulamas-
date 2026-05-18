# CLAUDE.md

AI coding agent için operasyonel referans. Detaylı dokümanlar `docs/agent/` altında.

## Project Summary

**Depo Yönetim Sistemi (WMS)** — Lot/palet takibi, putaway/pick görev akışları, üretim paleti kabul, mobil terminal PWA ve operatör performans (LMS) modülü içeren full-stack uygulama. FastAPI backend (Clean Architecture) + React/Vite frontend + Docker Compose dev stack + MySQL + bağımsız mikroservisler (WmsAiService, DocAiService, ExcelAiService, AgvSimService, DataGenService, AssistantAiService).

## Main Directories

- `BackendProje/` — FastAPI backend (Clean Architecture: api → application → core / infrastructure).
- `ReactProje/` — React 19 + Vite 7 frontend (PWA, TanStack Query). TypeScript yok.
- `WmsAiService/` — LangChain + Ollama doğal dil → SQL servisi (read-only view'lar) + doküman RAG asistanı (Chroma; ingestion'da LlamaIndex `MarkdownNodeParser`).
- `DocAiService/` — Belge AI mikroservisi (text PDF + VLM); irsaliye taslağı çıkarır, DB yazmaz.
- `ExcelAiService/` — AI destekli Excel yorumlama mikroservisi; pandas + LangChain `create_pandas_dataframe_agent` + Ollama, WMS hedef şemalarına sütun eşleme önerisi üretir. DB yazmaz.
- `AgvSimService/` — AGV/AMR simülasyonu (in-memory world, asyncio tick loop, A*/CA*).
- `DataGenService/` — Sentetik WMS veri üretici mikroservisi + Typer CLI; Backend REST API, RabbitMQ veya ML dosya çıktısına veri üretir. DB'ye doğrudan yazmaz.
- `AssistantAiService/` — Kullanıcı/rol bağlamlı, Human-in-the-Loop (HITL) depo asistanı; LangGraph + ChatOllama + AsyncSqliteSaver. LLM HITL aleti seçince `ProposedAction` döner, BackendProje `asistan_aksiyon_taslaklari` tablosuna yazar ve kullanıcı onayından sonra authoritative use case'i tetikler. DB'ye yazmaz; tek replica çalışır (SqliteSaver dosya kilidi).
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

### ExcelAiService

```bash
cd ExcelAiService
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8004
pytest
pytest -m unit
```

### DataGenService

```bash
cd DataGenService
uvicorn main:app --reload --host 127.0.0.1 --port 8005
python -m datagen --help
python -m datagen run timeseries_history --count 10 --target file
pytest -m unit
```

### AssistantAiService

```bash
cd AssistantAiService
pip install -r requirements-test.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8006
pytest                              # tum testler (FakeChatModel ile, Ollama gerekmez)
ruff check .
# Health (INTERNAL_API_KEY gerekli — host Ollama'nin ASSISTANT_LLM_MODEL'i cekili olmali)
curl -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8006/healthz
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
- AssistantAiService de tek replica çalışır (AsyncSqliteSaver dosya kilidi); horizontal scale yok. DB'ye dokunmaz — tüm yazımlar BackendProje `/api/asistan/*` üzerinden gider.
- AssistantAiService'e yeni bir tool eklerken: (a) AssistantAiService `app/application/agent/tools.py`'a `ToolSpec` (HITL ise executor=None), (b) BackendProje `app/application/services/asistan_tool_registry.py`'a authoritative executor — iki tarafta `tool_id`, `rbac_roles`, `args_schema` birebir aynı kalsın.
- Docker Compose çalışırken aynı servisleri ayrıca `uvicorn` ile başlatma — port çakışır.
- Backend değişikliği sonrası `ruff check .` + `pytest -m unit`; frontend sonrası `npm run lint`.
- `DOCS/rag/` altında doküman ekleme/değişimi sonrası **mutlaka** `cd WmsAiService && python ingest_docs.py --docs` çalıştırılmalı, ardından `pytest tests/test_rag_retrieval_quality.py` ile retrieval regresyonu doğrulanmalı. `verified: false` olarak işaretlenen dokümanlardaki belirsizlikler `DOCS/rag/_review/dogrulama-bekliyor.md` dosyasında toplanır; underscore prefix sayesinde indekslenmez.

## Important Notes

- Frontend: `http://localhost:5173`
- Backend docs: `http://localhost:8000/docs`
- Backend port: **8000**
- WmsAiService port: **8001**
- AgvSimService port: **8002**
- DocAiService port: **8003**
- ExcelAiService port: **8004**
- DataGenService port: **8005**
- AssistantAiService port: **8006**
- RabbitMQ AMQP: **5672** / Management UI: `http://localhost:15672` (`guest`/`guest`)
- Docker Compose project name: `depo-dev`
- Proje yolu ASCII olmalı: `D:\Ensar Dosya\DepoUygulamasi`
- Varsayılan VLM model (DocAi): `qwen3-vl:4b`
- Varsayılan WMS AI model: `qwen2.5-coder:7b`
- Varsayılan Asistan LLM (AssistantAi tool-calling): `qwen2.5-coder:7b` — kararsızlıkta `qwen2.5:7b-instruct` veya `llama3.1:8b-instruct` ile `ASSISTANT_LLM_MODEL` üzerinden swappable
- AssistantAiService taslak TTL: **15 dk** (`ASISTAN_DRAFT_TTL_SECONDS=900`); süresi dolan taslak onay endpoint'inde lazy şekilde `SURESI_DOLDU` durumuna çekilir
- `RABBITMQ_ENABLED=false` default — LMS event'leri için eski APScheduler 5dk polling aggregator çalışır. `true` yapıldığında relay + consumer worker akışı devreye girer; bkz. `docs/agent/rabbitmq-operations.md`.

## Do Not Touch

- `ReactProje/dist/`, `ReactProje/dev-dist/`, `ReactProje/stats.html` (build çıktıları)
- `__pycache__/`, `.venv/`, `venv/`, `.coverage`
- `BackendProje/alembic/versions/` — sadece Alembic ile oluştur, elle düzenleme.
- `WmsAiService/wms_chroma_db/` — ChromaDB persistent store (generated).
- `assistant_ai_state` Docker volume'u — AssistantAiService SqliteSaver dosyası; sadece compose ile yönet, elle silme/düzenleme yapma.
- Standalone `migrate_*.py` scriptleri idempotent değil; tekrar çalıştırma.

## More Detailed Documentation

- Mimari detayları: `docs/agent/project-architecture.md`
- Docker detayları: `docs/agent/docker-compose.md`
- Backend detayları: `docs/agent/backend-notes.md`
- Frontend detayları: `docs/agent/frontend-notes.md`
- AI servis detayları: `docs/agent/ai-services.md`
- DataGenService runbook: `DOCS/agent/data-gen-service.md`
- AssistantAiService entegrasyon planı: `DOCS/ASSISTANT_AI_SERVICE_ENTEGRASYON_PLANI.md`
- Excel AI entegrasyon planı: `DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md`
- Ortam değişkenleri: `docs/agent/env-reference.md`
- RabbitMQ operasyon ve runbook: `docs/agent/rabbitmq-operations.md`
