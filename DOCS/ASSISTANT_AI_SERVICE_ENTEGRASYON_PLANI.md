# AssistantAiService Entegrasyon Planı

> **Durum:** Onay bekliyor — uygulamaya başlamadan önce CLAUDE.md'deki port, mimari ve isimlendirme kurallarına uyum doğrulanacak.
> **Hedef:** Kullanıcı/rol bağlamı taşıyan, insan onaylı aksiyon (Human-in-the-Loop) yapabilen depo asistanı mikroservisini WMS ekosistemine eklemek.
> **Sorumluluk sınırı:** `AssistantAiService` **DB'ye dokunmaz**; authoritative tüm yazımlar `BackendProje` üzerinden gerçekleşir (DocAi / ExcelAi felsefesiyle uyumlu).

---

## 1. Mimari Karar Özeti

| Konu | Karar |
|---|---|
| Servis | Bağımsız `AssistantAiService` (port **8006**, compose servisi `assistant-ai`) |
| Framework | FastAPI + **LangGraph** (StateGraph, `tools_condition`) + LangChain `bind_tools` |
| LLM | `ChatOllama` — varsayılan `qwen2.5-coder:7b`; env'den `ASSISTANT_LLM_MODEL` ile swappable |
| State / hafıza | LangGraph **SqliteSaver** — container içinde `/data/assistant_state.sqlite` (named volume `assistant_ai_state`) |
| Draft store | Backend'de **yeni Alembic migration**: `asistan_aksiyon_taslaklari` (TTL + idempotency_key + audit) |
| Tool mimarisi | LLM yalnız `tool_id` + `params` üretir. Backend'de **tool registry** (`tool_id → use_case`) onay endpoint'inde execute eder |
| Auth | Frontend → `BackendProje /api/asistan/*` (Bearer JWT + `require_role`) → AssistantAiService (`X-Internal-Api-Key`). AssistantAi servisi **JWT doğrulamaz**; Backend authoritative |
| Context enjeksiyonu | Backend, JWT'den `user_id, rol`'u; aktif görev/ekranı request'ten alıp `UserContext` blob'u halinde upstream'e iletir; system prompt'a interpolate edilir |
| UI | Yeni sayfa `/depo-asistani` → `pages/DepoAsistaniPage.jsx` (+ sidebar girişi, feature flag `VITE_FEATURE_DEPO_ASISTANI_ENABLED`) |
| Observability | Mevcut `langfuse_tracing.py` deseninin kopyası (Langfuse opsiyonel, no-op fallback) |
| Roller | v1: `admin`, `lojistik`, `depocu` erişebilir. Tool seti **rol-bazlı registry** ile filtrelenir |
| Draft TTL | 15 dakika (env'den ayarlanabilir: `ASISTAN_DRAFT_TTL_SECONDS`) |

### Karar gerekçeleri

- **Backend tool registry** seçildi çünkü DocAi/ExcelAi pattern'iyle birebir uyumlu, AI servisi DB credential taşımıyor, audit trail tek noktada (Backend) toplanıyor.
- **LangGraph + SqliteSaver** seçildi çünkü Redis altyapısı stack'te yok, in-memory ise restart'ta hafıza sıfırlar. SQLite container volume ile kalıcı, ileride Redis/Postgres checkpointer'a swap edilebilir tek dosya değişikliğiyle.
- **`qwen2.5-coder:7b`** varsayılan: zaten Ollama'da çekili (WmsAi/ExcelAi kullanıyor). Tool calling kararsızlık görülürse env üzerinden `qwen2.5:7b-instruct` veya `llama3.1:8b-instruct` ile değiştirilecek.

---

## 2. Uygulama Planı (Aşamalı)

### Faz 0 — Iskelet (yarım gün)

1. `AssistantAiService/` dizini oluştur (boş Python paketi, `requirements.txt`).
2. `compose.yml`'a `assistant-ai` servisi ekle:
   - port 8006
   - healthcheck `/healthz`
   - env: `INTERNAL_API_KEY`, `OLLAMA_BASE_URL`, `ASSISTANT_LLM_MODEL`, `BACKEND_BASE_URL`
   - volume `assistant_ai_state:/data`
3. `infra/env/dev.env`'e yeni env'ler:
   - `ASSISTANT_AI_SERVICE_URL=http://assistant-ai:8006`
   - `ASSISTANT_AI_SERVICE_TIMEOUT=120`
   - `ASSISTANT_LLM_MODEL=qwen2.5-coder:7b`
   - `FEATURE_DEPO_ASISTANI_ENABLED=true`
   - `VITE_FEATURE_DEPO_ASISTANI_ENABLED=true`
   - `ASISTAN_DRAFT_TTL_SECONDS=900`
   - `SQLITE_CHECKPOINT_PATH=/data/assistant_state.sqlite`
4. `/healthz` endpoint + `X-Internal-Api-Key` middleware (DocAi/ExcelAi'den port).

### Faz 1 — Backend authoritative katmanı (1 gün)

1. **Alembic migration**: `asistan_aksiyon_taslaklari` tablosu
   - `id UUID PK`
   - `user_id FK kullanicilar.id`
   - `rol VARCHAR(32)`
   - `tool_id VARCHAR(64)`
   - `payload_json JSON`
   - `status ENUM('beklemede','onaylandi','reddedildi','suresi_doldu')`
   - `idempotency_key VARCHAR(128) UNIQUE`
   - `created_at`, `expires_at`, `executed_at`
   - index: `(user_id, status)`, `(expires_at)`
2. **Tool registry**: `app/application/services/asistan_tool_registry.py`
   - `tool_id → ToolSpec(use_case_factory, schema_validator, rbac_roles, hitl: bool)`
3. **Use case'ler**: `app/application/use_cases/asistan_use_cases.py`
   - `ChatProxyKullanimi` — bağlam topla, AssistantAi'ye gönder, cevabı normalize et
   - `TaslakOlustur`, `TaslakOnayla`, `TaslakReddet`, `TaslakListele`
   - HITL=false tool'lar taslak yaratmadan direkt execute olur
4. **Router**: `app/api/v1/routers/asistan.py`
   - `POST /api/asistan/chat`
   - `GET /api/asistan/taslaklar`
   - `POST /api/asistan/taslaklar/{id}/onayla`
   - `POST /api/asistan/taslaklar/{id}/reddet`
5. **İstemci**: `app/infrastructure/services/assistant_ai_client.py` (httpx, tipli hata sınıfları — ExcelAiClient'ten port).
6. **DI**: yeni modül `app/infrastructure/di/modules/asistan.py`, `container.py`'den re-export.
7. **Backend testleri** (`tests/test_asistan_*`): tool registry RBAC, taslak onay/reddet idempotency, expires_at davranışı, audit.

### Faz 2 — AssistantAiService çekirdek (1.5 gün)

1. `main.py` → FastAPI + lifespan (Langfuse flush, SqliteSaver dispose).
2. `agent/graph.py` → LangGraph `StateGraph`:
   - nodes: `prepare_context → llm → tools_condition → tool_executor → llm` döngüsü
   - HITL tool'lar `__draft__` sentinel'i bırakır, döngüden END'e çıkar
3. `agent/tools.py` → LangChain `@tool` tanımları (HITL tool'lar gerçek iş yapmaz, `ProposedAction` döner).
4. `agent/prompts.py` → katı sistem promptu (Türkçe, 7B uyumlu few-shot, JSON disiplini, "kullanıcı onayı zorunlu" pasaj).
5. `agent/state.py` → `AssistantState` TypedDict (messages, user_context, pending_drafts, route).
6. `runtime/checkpointer.py` → SqliteSaver init + thread_id = `f"{user_id}:{session_id}"`.
7. `runtime/llm.py` → `get_llm()` factory (env'den swap).
8. `api/chat.py` → `POST /api/asistan/chat`.
9. `api/health.py`.
10. `observability/langfuse_tracing.py` (WmsAi'den port).
11. `tests/` → graph birim testleri (mock LLM), tool serialization, HITL kesimi.

### Faz 3 — Frontend (1 gün)

1. `services/depoAsistaniApi.js` → `postChat`, `getTaslaklar`, `onaylaTaslak`, `reddetTaslak`.
2. `queries/depoAsistaniQueries.js` → `queryKeys.depoAsistani.*`, mutation hook'ları.
3. `pages/DepoAsistaniPage.jsx` → chat layout (mesaj listesi + input + "ekran bağlamı" rozeti).
4. `components/depoAsistani/`:
   - `ChatMesaj.jsx`
   - `TaslakKart.jsx` (Onayla / Reddet butonlu özel mesaj tipi)
   - `BaglamRozeti.jsx`
   - `AsistanInput.jsx`
5. Sidebar girişi + `App.jsx` route (`RoleRoute` ile `admin`, `lojistik`, `depocu`).
6. Feature flag (`VITE_FEATURE_DEPO_ASISTANI_ENABLED`) kapalıyken menüde görünmez.

### Faz 4 — Doğrulama & dokümantasyon (yarım gün)

1. `docker compose up --build assistant-ai backend frontend` → e2e duman testi.
2. `ruff check .` + `pytest -m unit` (backend), `npm run lint` (frontend), `pytest` (AssistantAiService).
3. `DOCS/agent/ai-services.md` güncelle.
4. `DOCS/agent/env-reference.md` + `docs/agent/docker-compose.md` + kök `README.md` servis tablosuna `assistant-ai:8006` ekle.
5. `CLAUDE.md` "Common Commands" + "Servisler ve Portlar" + "Important Notes" güncellemesi.

**Tahmini toplam:** ~4 iş günü (LLM tool-calling tuning hariç).

---

## 3. v1 Tool Seti

| tool_id | Tür | RBAC | Açıklama |
|---|---|---|---|
| `stok_sorgula` | read-only | admin, lojistik, depocu | Ürün/lokasyon/lot için anlık stok |
| `gorevlerim_listele` | read-only | admin, lojistik, depocu | Kullanıcının açık putaway/pick görevleri |
| `vardiya_metriklerim` | read-only | admin, lojistik, depocu | LMS vardiya KPI'ları |
| `yerlestirme_konum_degistir` | **HITL** | admin, lojistik, depocu | Bekleyen yerleştirme görevinin hedef konumunu değiştir |
| `siparis_oncelik_degistir` | **HITL** | admin, lojistik | Sipariş öncelik güncelleme |
| `siparis_iptal` | **HITL** | admin, lojistik | Sipariş iptali (depocu görmez) |

---

## 4. AssistantAiService Dizin Ağacı

```text
AssistantAiService/
|-- README.md                          Servis ozeti, calistirma, env, HITL akis semasi
|-- requirements.txt                   fastapi, uvicorn, langchain, langgraph, langchain-ollama,
|                                      langchain-community, langgraph-checkpoint-sqlite,
|                                      httpx, python-dotenv, pydantic-settings, langfuse (opsiyonel)
|-- requirements-test.txt              pytest, pytest-asyncio, respx (httpx mock), freezegun
|-- main.py                            FastAPI app, lifespan (langfuse flush, sqlite dispose),
|                                      router register, INTERNAL_API_KEY middleware
|-- config.py                          pydantic-settings: OLLAMA_BASE_URL, ASSISTANT_LLM_MODEL,
|                                      INTERNAL_API_KEY, BACKEND_BASE_URL, SQLITE_CHECKPOINT_PATH,
|                                      MAX_TOOL_ITERATIONS, MAX_HISTORY_TURNS, LANGFUSE_*
|
|-- api/
|   |-- __init__.py
|   |-- chat.py                        POST /api/asistan/chat. Soru + UserContext + session_id alir,
|   |                                  graph.invoke cagirir, ChatResponse doner (cevap | draft | tool_log)
|   |-- health.py                      GET /healthz, /readyz (sqlite + ollama ping)
|   `-- schemas.py                     Pydantic: ChatRequest, ChatResponse, UserContext, ProposedAction
|
|-- agent/
|   |-- __init__.py
|   |-- graph.py                       LangGraph StateGraph kurulumu: prepare_context -> llm_node ->
|   |                                  tools_condition -> tool_executor -> llm_node. HITL tool'larda
|   |                                  ProposedAction'i state.pending_drafts'a koyup END'e gider
|   |-- state.py                       TypedDict AssistantState{messages, user_context,
|   |                                  pending_drafts: list[ProposedAction], route, debug}
|   |-- prompts.py                     SYSTEM_PROMPT (Turkce, kati, few-shot), context_injector,
|   |                                  tool secimi disiplini, JSON sema ornekleri
|   |-- tools.py                       LangChain @tool: stok_sorgula, gorevlerim_listele,
|   |                                  vardiya_metriklerim, yerlestirme_konum_degistir (HITL),
|   |                                  siparis_oncelik_degistir (HITL), siparis_iptal (HITL).
|   |                                  HITL tool'lar gercek API cagirmaz; ProposedAction doner
|   |-- nodes.py                       prepare_context_node, llm_node, tool_executor_node helper'lari
|   `-- routing.py                     custom router: tools_condition + hitl_short_circuit
|
|-- runtime/
|   |-- __init__.py
|   |-- llm.py                         get_llm() ChatOllama factory, bind_tools, model swap
|   |-- checkpointer.py                get_checkpointer() SqliteSaver singleton, thread_id helper
|   `-- backend_client.py              Backend read-only tool'lari icin httpx client (stok_sorgula
|                                      vb. -> /api/asistan/tool-exec/{tool_id} read-only endpoint).
|                                      HITL tool'lari icin kullanilmaz
|
|-- observability/
|   |-- __init__.py
|   `-- langfuse_tracing.py            WmsAiService'ten port: trace_span, summarize_text, flush,
|                                      opsiyonel env kapaliysa no-op
|
|-- security/
|   |-- __init__.py
|   `-- api_key.py                     X-Internal-Api-Key middleware/dependency (DocAi pattern)
|
|-- tests/
|   |-- __init__.py
|   |-- conftest.py                    FakeListChatModel fixture, in-memory SqliteSaver, sample contexts
|   |-- test_health.py                 /healthz auth + payload
|   |-- test_graph_readonly.py         Read-only tool akisi: stok_sorgula cagriliyor mu, cevap render
|   |-- test_graph_hitl.py             HITL tool cagrisi ProposedAction doner, dongu kapanir
|   |-- test_prompt_context.py         user_context system prompt'a dogru enjekte oluyor mu
|   |-- test_tools_rbac.py             depocu rolunde siparis_iptal tool listesinde olmuyor
|   |-- test_checkpointer.py           Ayni session_id'de history korunuyor
|   `-- test_api_key.py                X-Internal-Api-Key eksik -> 401/503
|
`-- Dockerfile.note.md                 "Bu servis infra/docker/python-service.Dockerfile kullanir
                                       SERVICE_DIR=AssistantAiService build-arg ile" notu
```

---

## 5. Backend Tarafında Eklenecek/Değişecek Dosyalar

```text
BackendProje/
|-- alembic/versions/
|   `-- <yeni_hash>_asistan_aksiyon_taslaklari.py    Yeni tablo + indexler
|-- app/
|   |-- core/entities/
|   |   `-- asistan_aksiyon_taslagi.py               Domain entity
|   |-- core/repositories/
|   |   `-- asistan_aksiyon_taslagi_repository.py    Soyut interface
|   |-- application/dto/
|   |   `-- asistan_dto.py                           Chat, ProposedAction, OnayResponse DTO'lari
|   |-- application/services/
|   |   `-- asistan_tool_registry.py                 tool_id -> use_case + RBAC + JSON Schema
|   |-- application/use_cases/
|   |   `-- asistan_use_cases.py                     ChatProxy, TaslakOlustur/Onayla/Reddet/Listele
|   |-- infrastructure/persistence/repositories/
|   |   `-- sqlalchemy_asistan_aksiyon_taslagi_repository.py
|   |-- infrastructure/di/modules/
|   |   `-- asistan.py                               Factory'ler
|   |-- infrastructure/di/container.py               +re-export
|   |-- infrastructure/services/
|   |   `-- assistant_ai_client.py                   httpx client + tipli hatalar
|   `-- api/v1/routers/
|       `-- asistan.py                               /api/asistan/chat + /taslaklar/*
|-- models.py                                        +AsistanAksiyonTaslagi ORM
`-- tests/
    |-- test_asistan_router.py
    |-- test_asistan_tool_registry.py
    `-- test_asistan_use_cases.py
```

---

## 6. Frontend Tarafında Eklenecek Dosyalar

```text
ReactProje/src/
|-- services/depoAsistaniApi.js
|-- queries/depoAsistaniQueries.js                   queryKeys.depoAsistani.*
|-- pages/DepoAsistaniPage.jsx
|-- components/depoAsistani/
|   |-- ChatMesaj.jsx
|   |-- TaslakKart.jsx                               Onayla / Reddet butonlari, payload diff goster
|   |-- BaglamRozeti.jsx                             "aktif gorev #123 putaway" rozeti
|   `-- AsistanInput.jsx
`-- App.jsx                                          +route (admin, lojistik, depocu)
```

---

## 7. HITL Akış Şeması

```text
[Frontend]                  [BackendProje]                  [AssistantAiService]
   |                              |                                |
   |--POST /api/asistan/chat----->|                                |
   |  Bearer JWT                  |                                |
   |  body: {soru, session_id,    |                                |
   |    aktif_gorev_id, ekran}    |                                |
   |                              |--build UserContext------------>|
   |                              |  X-Internal-Api-Key            |
   |                              |  + UserContext + soru          |
   |                              |                                |
   |                              |                          [LangGraph]
   |                              |                          llm -> bind_tools
   |                              |                          tool: yerlestirme_konum_degistir (HITL)
   |                              |                          tool body: ProposedAction
   |                              |                                |
   |                              |<--ChatResponse-----------------|
   |                              |  {type: "draft", proposed_action}
   |                              |                                |
   |                              |--TaslakOlustur use case        |
   |                              |  insert asistan_aksiyon_       |
   |                              |  taslaklari                    |
   |                              |                                |
   |<--ChatResponse---------------|                                |
   |  {type: "draft", taslak_id,  |                                |
   |   ozet, payload}             |                                |
   |                              |                                |
   |  [Kullanici "Onayla" basar]  |                                |
   |--POST /api/asistan/          |                                |
   |  taslaklar/{id}/onayla------>|                                |
   |                              |--tool_registry[tool_id]        |
   |                              |  .execute(payload)             |
   |                              |  -> ilgili use case            |
   |                              |  -> MySQL                      |
   |                              |                                |
   |<--OnayResponse---------------|                                |
   |  {status: "onaylandi",       |                                |
   |   sonuc: {...}}              |                                |
```

---

## 8. Açık Riskler ve Notlar

- **7B model tool-calling kararsızlığı:** `qwen2.5-coder:7b` JSON şemasından sapma yaparsa, retry + JSON repair + few-shot ile mitigasyon. Gerekirse `qwen2.5:7b-instruct` veya `llama3.1:8b-instruct` swap'i (tek env değişikliği).
- **SqliteSaver tek-süreç:** AssistantAi servisi de AgvSimService gibi tek replica çalışmalı. Compose'da `deploy.replicas: 1` not'u açıkça yazılacak.
- **Draft TTL temizliği:** APScheduler ile saatlik `expired_draft_cleanup` job'u (Backend tarafında).
- **Audit:** `asistan_aksiyon_taslaklari` tablosu tüm önerileri (reddedilenler dahil) saklar; `sistem_loglari` ile bağlanır.
- **Frontend F5 davranışı:** Bekleyen taslaklar `GET /api/asistan/taslaklar?status=beklemede` ile sayfa yüklemesinde geri çekilir; chat mesaj geçmişi yalnız aktif sekme süresince in-memory tutulur (LangGraph thread_id ile sunucu tarafında kalıcı).

---

## 9. Doğrulama Komutları (Faz 4)

```bash
# AssistantAiService unit testleri
cd AssistantAiService && pytest -m unit

# Backend ek testleri
cd BackendProje && ruff check . && pytest -m unit tests/test_asistan_*

# Frontend lint
cd ReactProje && npm run lint

# E2E duman testi
docker compose up -d --build assistant-ai backend frontend
curl -H "X-Internal-Api-Key: $INTERNAL_API_KEY" http://localhost:8006/healthz
```

---

## 10. Sonraki Adımlar (Onay Sonrası)

1. Faz 0 iskelet PR (compose + env + boş paket + healthz).
2. Faz 1 Backend authoritative katman PR (migration + tool registry + router + tests).
3. Faz 2 AssistantAiService çekirdek PR (graph + tools + tests).
4. Faz 3 Frontend PR (sayfa + draft kartı + feature flag).
5. Faz 4 Dokümantasyon & smoke test PR (README/CLAUDE.md/env-reference güncellemeleri).
