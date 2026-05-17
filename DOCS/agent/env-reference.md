# Environment Variables Reference

Tüm servis env'leri. CLAUDE.md, bu dosyaya işaret eder.

## BackendProje (`BackendProje/.env`)

Şablon: `.env.example`.

**Zorunlu:**
- `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`
- `JWT_SECRET_KEY` (min 32 karakter)

**Test (`BackendProje/.env.test`):**
- `DB_NAME` mutlaka `depo_db_test` olmalı (`test` ifadesi içermezse güvenlik kontrolü hata verir).

**Feature flag'ler:**
- `FEATURE_URETIM_PALET_PILOT_DEPO_IDS` — boş=kapalı, `TUMU`=tüm depolar, `1,3,5`=belirli depolar.
- `FEATURE_AGV_DISPATCH_DEPO_IDS` — aynı şema.
- `FEATURE_DOC_AI_PILOT_DEPO_IDS` — aynı şema.

**Palet veri kaynağı:**
- `PALET_VERI_KAYNAGI` — `LOCAL`, `MOCK`, `ERP`.

**Migration drift kontrolü (LMS):**
- `DEPO_STRICT_MIGRATION=1` → drift halinde startup'ı durdur (production önerilir).
- `DEPO_SKIP_MIGRATION_CHECK=1` → kontrolü atla (acil durum).

**Entegrasyonlar:**
- `AGV_SIM_SERVICE_URL` (def `http://127.0.0.1:8002`), `AGV_SIM_SERVICE_TIMEOUT` (def `2.0`).
- `DOC_AI_SERVICE_URL` (local def `http://127.0.0.1:8003`), `DOC_AI_SERVICE_TIMEOUT`.
- `EXCEL_AI_SERVICE_URL` (local def `http://127.0.0.1:8004`), `EXCEL_AI_SERVICE_TIMEOUT` (def `180`).
- `FEATURE_EXCEL_AI_ENABLED` (def `false`) — bool; `true` ile `/api/excel-ai/*` proxy router aktiflesir, aksi halde 404.
- `INTERNAL_API_KEY` — AGV, DocAi ve ExcelAi ile **paylaşılan** shared secret.

**RabbitMQ (LMS event hattı):**
- `RABBITMQ_ENABLED` (def `false`) — `true` ile relay + consumer worker akışı, `false` ile eski 5dk APScheduler aggregator.
- `RABBITMQ_URL` (def `amqp://guest:guest@localhost:5672/`; compose: `amqp://guest:guest@rabbitmq:5672/`).
- `RABBITMQ_EXCHANGE` (def `depo.events`).
- `RABBITMQ_QUEUE` (def `depo.lms.operator_metrikleri`).
- `RABBITMQ_DLX` (def `depo.events.dlx`).
- `RABBITMQ_PREFETCH` (def `20`) — consumer prefetch sayısı.
- `RABBITMQ_RELAY_BATCH_SIZE` (def `100`) — outbox relay batch.
- Detaylı operasyon: `docs/agent/rabbitmq-operations.md`.

## WmsAiService (`WmsAiService/.env`)

**Zorunlu:** `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME` (`depo_ai_reader` read-only kullanıcı önerilir).

**Opsiyonel:**
- `OLLAMA_MODEL` (def `qwen2.5-coder:7b`)
- `OLLAMA_BASE_URL` (def `http://localhost:11434`)
- `OLLAMA_ANSWER_MODEL`
- `LLM_TEMPERATURE` (def `0`)
- `LLM_NUM_CTX` (def `4096`)
- `LLM_TIMEOUT` (def `120`)
- `MAX_CORRECTION_ATTEMPTS` (def `2`)
- `ANSWER_NUM_PREDICT` (def `40`)
- `FEW_SHOT_K` (def `3`)
- `CHROMA_PERSIST_DIR` (def `./wms_chroma_db`)
- `EMBEDDING_MODEL` (def `sentence-transformers/all-MiniLM-L6-v2`)
- `ROUTER_COLLECTION_NAME` (def `wms_ai_router_intents`)
- `DOCS_COLLECTION_NAME` (def `wms_ai_docs_chunks`)
- `ROUTER_TOP_K`, `ROUTER_CONFIDENCE_THRESHOLD`, `ROUTER_CONFIDENCE_MARGIN`
- `RAG_TOP_K` (def 4), `RAG_STRICT_DISTANCE` (def 0.9; en iyi chunk bu esigin uzerindeyse LLM cagrilmaz, "bilgi bulamadim" doner), `RAG_MAX_DISTANCE` (def 1.05; bu esige kadar olan chunk'lar baglama dahil edilir), `RAG_NUM_PREDICT` (def 300)

## AgvSimService (`AgvSimService/.env`)

**Zorunlu:**
- `INTERNAL_API_KEY` (BackendProje ile aynı).

**Opsiyonel:**
- `WMS_BASE_URL` (def `http://127.0.0.1:8000`)
- `TICK_HZ` (def `2`)
- `CORS_ALLOW_ORIGINS` (def `https://localhost:5173`)
- `GRID_JSON_PATH` (def `./data/depo_1_grid.json`)
- `WS_MAX_QUEUE` (def `32`)

## DocAiService (`DocAiService/.env`)

**Zorunlu:**
- `INTERNAL_API_KEY` (BackendProje ile aynı).

**Opsiyonel:**
- `WMS_BASE_URL` (def `http://127.0.0.1:8000`)
- `OLLAMA_BASE_URL` (def `http://127.0.0.1:11434`)
- `OLLAMA_TEXT_MODEL`
- `OLLAMA_VLM_MODEL` (image input desteklemelidir; örn `qwen3-vl:4b`)
- `LLM_TIMEOUT`
- `MAX_FILE_SIZE_MB`
- `CORS_ALLOW_ORIGINS`

## ExcelAiService (`ExcelAiService/.env`)

**Zorunlu:**
- `INTERNAL_API_KEY` (BackendProje ile aynı).

**Opsiyonel:**
- `WMS_BASE_URL` (def `http://127.0.0.1:8000`)
- `OLLAMA_BASE_URL` (def `http://127.0.0.1:11434`)
- `OLLAMA_TEXT_MODEL` (def `qwen2.5-coder:7b`; pandas agent için code-tuned model önerilir)
- `LLM_TIMEOUT` (def `120`)
- `MAX_FILE_SIZE_MB` (def `10`)
- `MAX_ROWS` (def `10000`) — tek sayfada okunan maksimum satır
- `MAX_SHEETS` (def `10`) — kabul edilen maksimum sayfa sayısı
- `IDEMPOTENCY_TTL_SECONDS` (def `3600`) — in-memory LRU cevap cache TTL
- `IDEMPOTENCY_MAX_ENTRIES` (def `256`)
- `CORS_ALLOW_ORIGINS` (def `https://localhost:5173`)

## Langfuse Cloud (`WmsAiService`, `DocAiService`, `ExcelAiService`)

Langfuse bu projede Cloud hedefiyle kullanilir. Self-host bu planin kapsami disindadir; gerekirse ayri operasyon plani gerekir.

**Kurulum:**
- Langfuse Cloud account ve project olustur.
- Project settings altindan public/secret key al.
- `infra/env/langfuse.local.example` dosyasini `infra/env/langfuse.local` olarak kopyala.
- EU region icin `LANGFUSE_BASE_URL=https://cloud.langfuse.com`, US region icin `LANGFUSE_BASE_URL=https://us.cloud.langfuse.com` kullan.
- AI servislerini yenile: `docker compose up -d --build wms-ai doc-ai excel-ai`.

**Opsiyonel:**
- `LANGFUSE_TRACING_ENABLED` (def `false`) — tracing ac/kapat.
- `LANGFUSE_PUBLIC_KEY` — Langfuse Cloud project public key.
- `LANGFUSE_SECRET_KEY` — Langfuse Cloud project secret key; `infra/env/dev.env` icine yazma.
- `LANGFUSE_BASE_URL` — Cloud region endpoint'i.
- `LANGFUSE_TRACING_ENVIRONMENT` (def `development`) — trace environment etiketi.
- `LANGFUSE_SAMPLE_RATE` (def `1.0`) — trace sampling orani.
- `LANGFUSE_CAPTURE_PAYLOADS` (def `false`) — raw prompt/output yerine sanitize edilmis ozet politikasi.
- `LANGFUSE_RELEASE` — opsiyonel release/version etiketi.

**Guvenlik:**
- Gercek key'ler sadece git tarafindan ignore edilen `infra/env/langfuse.local` icinde tutulur.
- Base64 image, belge icerigi, dosya ham verisi, e-posta, telefon ve vergi/kimlik benzeri numaralar maskelenir.
- Langfuse erisilemezse servis request'i basarisiz olmaz; hata sadece loglanir.

## DataGenService (`DataGenService/.env`)

Sentetik veri uretici servisidir; DB'ye dogrudan yazmaz.

**REST hedefleri icin zorunlu:**
- `BACKEND_BASE_URL` — Backend FastAPI tabani (compose: `http://backend:8000`, local: `http://127.0.0.1:8000`).
- `DATAGEN_ADMIN_USERNAME` — Backend login kullanicisi (dev seed: `admin`).
- `DATAGEN_ADMIN_PASSWORD` — Backend login sifresi (dev seed: `admin123`).

**Opsiyonel:**
- `JWT_REFRESH_BUFFER_SEC` (def `60`) — token bitmeden refresh tamponu.
- `RABBITMQ_URL` (compose: `amqp://guest:guest@rabbitmq:5672/`) — `task_load --target=rabbit` icin.
- `RABBITMQ_EXCHANGE` (def `depo.events`).
- `DEFAULT_SEED` (def `42`).
- `LOCALE` (def `tr_TR`).
- `OUTPUT_DIR` (compose: `/workspace/ml_models/talep_tahmin/data/raw`) — `timeseries_history --target=file` cikti dizini.
- `BATCH_SIZE` (def `500`).
- `CONCURRENCY` (def `10`).
- `HTTP_TIMEOUT_SEC` (def `30`).
- `HTTP_MAX_RETRIES` (def `3`).

## ReactProje (`ReactProje/.env.local`)

İsteğe bağlı.

- `VITE_DEV_HTTPS` — `true`/`false` (Compose default `false`, manuel local `true` önerilir).
- `VITE_BACKEND_PROXY_TARGET` — Compose: `http://backend:8000`, local: `http://127.0.0.1:8000`.
- `VITE_FEATURE_AGV_ENABLED=true` — `/agv-izleme` route + sidebar item açar.
- `VITE_FEATURE_DOC_AI_ENABLED=true` — DocAI UI özelliklerini açar.
- `VITE_FEATURE_EXCEL_AI_ENABLED=true` — AI Asistan → Excel Analizi (`/ai-asistan/excel`) sidebar girişini açar.

## Docker Compose

- Tracked dev env: `infra/env/dev.env`.
- Optional Langfuse Cloud env: `infra/env/langfuse.local` (`infra/env/langfuse.local.example` dosyasindan turetilir, git'e alinmaz).
- Kişisel override / secret: `infra/env/*.local` veya `infra/env/*.secret` (git'e alınmaz).
- Compose project name: `depo-dev`.
