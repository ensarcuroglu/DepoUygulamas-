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
- `INTERNAL_API_KEY` — AGV ve DocAi ile **paylaşılan** shared secret.

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

## ReactProje (`ReactProje/.env.local`)

İsteğe bağlı.

- `VITE_DEV_HTTPS` — `true`/`false` (Compose default `false`, manuel local `true` önerilir).
- `VITE_BACKEND_PROXY_TARGET` — Compose: `http://backend:8000`, local: `http://127.0.0.1:8000`.
- `VITE_FEATURE_AGV_ENABLED=true` — `/agv-izleme` route + sidebar item açar.
- `VITE_FEATURE_DOC_AI_ENABLED=true` — DocAI UI özelliklerini açar.

## Docker Compose

- Tracked dev env: `infra/env/dev.env`.
- Kişisel override / secret: `infra/env/*.local` veya `infra/env/*.secret` (git'e alınmaz).
- Compose project name: `depo-dev`.
