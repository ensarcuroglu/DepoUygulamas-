# Langfuse Cloud Observability Entegrasyon Plani

## Approach

Langfuse entegrasyonu yalnizca Langfuse Cloud hedeflenerek uygulanmistir. WmsAiService, DocAiService ve ExcelAiService LLM cagrilari Cloud projesinden alinan API key'lerle izlenecek; tracing kapaliysa veya key yoksa servis davranisi degismeyecek. WmsAiService ve ExcelAiService icin LangChain `CallbackHandler`, DocAiService icin manuel `generation/span` gozlemleri kullanilir.

## Scope

- In:
  - `WmsAiService`, `DocAiService`, `ExcelAiService` LLM cagri tracing'i.
  - Langfuse Cloud env degiskenleri, client-side masking, sampling ve shutdown flush.
  - `DOCS/agent/ai-services.md`, `DOCS/agent/env-reference.md`, README kisa notlari.
  - Optional `infra/env/langfuse.local` kullanim akisi ve tracked `infra/env/langfuse.local.example`.
- Out:
  - Backend/Frontend UI degisikligi.
  - Prompt management, eval datasetleri, score workflow'lari.
  - Self-host Langfuse kurulumu. Bu planda kapsam disidir; ileride ayri operasyon plani gerekir.

## Langfuse Cloud Setup

- **Varsayilan hedef:** Langfuse Cloud EU region, `LANGFUSE_BASE_URL=https://cloud.langfuse.com`.
- **US region hedefi:** Langfuse projesi US region'da acildiysa `LANGFUSE_BASE_URL=https://us.cloud.langfuse.com`.
- **Ucretsiz baslangic:** Langfuse Cloud Hobby plani ucretsiz baslangic icin kullanilacak. 2026-05-17 itibariyla kredi karti gerektirmeden 50k units/ay, 30 gun veri erisimi ve 2 kullanici sunuyor.
- **Kurulum akisi:**
  - Langfuse Cloud account ve project olustur.
  - Project settings altindan `LANGFUSE_PUBLIC_KEY` ve `LANGFUSE_SECRET_KEY` al.
  - `infra/env/langfuse.local.example` dosyasini `infra/env/langfuse.local` olarak kopyala.
  - Region'a gore `LANGFUSE_BASE_URL` degerini sec.
  - `docker compose up -d --build wms-ai doc-ai excel-ai` ile AI servislerini yenile.

## Public Interfaces / Config

- Uc servise `langfuse` dependency'si eklenecek.
- Ortak env'ler:
  - `LANGFUSE_TRACING_ENABLED=false` default.
  - `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL`.
  - `LANGFUSE_TRACING_ENVIRONMENT=development`.
  - `LANGFUSE_SAMPLE_RATE=1.0`.
  - `LANGFUSE_CAPTURE_PAYLOADS=false` custom guvenlik anahtari.
  - `LANGFUSE_RELEASE` opsiyonel.
- Compose `x-python-common.env_file` altinda optional `./infra/env/langfuse.local` okunacak.
- Secret'lar tracked `infra/env/dev.env` icine yazilmayacak; gercek key'ler sadece ignored `infra/env/langfuse.local` icinde tutulacak.
- HTTP response sozlesmeleri degismeyecek; trace id ilk fazda response'a eklenmeyecek.

## Privacy and Safety

- `LANGFUSE_CAPTURE_PAYLOADS=false` default kalacak.
- Prompt/output/raw JSON Langfuse Cloud'a sadece sanitize edilmis ozet olarak gonderilecek.
- Base64 image, belge icerigi, dosya ham verisi, e-posta, telefon, vergi/kimlik benzeri numaralar maskelenecek.
- Langfuse network/API hatasi request'i dusurmeyecek; sadece loglanacak.
- Langfuse health check zorunlulugu eklenmeyecek.

## Action Items

[x] Revise existing `DOCS/LANGFUSE_AI_OBSERVABILITY_PLANI.md` for Langfuse Cloud-only usage.

[x] Add optional `./infra/env/langfuse.local` to `x-python-common.env_file` in `compose.yml`.

[x] Add tracked `infra/env/langfuse.local.example` with Cloud EU/US base URL guidance and placeholder keys.

[x] Add a small Langfuse helper in each service style: `WmsAiService/langfuse_tracing.py`, `DocAiService/app/infrastructure/observability/langfuse_tracing.py`, and `ExcelAiService/app/infrastructure/observability/langfuse_tracing.py`.

[x] Implement helper behavior: env-based enable/disable, `get_client()`, `CallbackHandler` factory, no-op context manager, `flush()`, safe metadata builder, and masking/truncation for prompts, JSON payloads, file names, base64 images, emails/phones/tax-like numbers.

[x] Instrument WmsAiService: wrap `/api/ai/sorgula` and `/api/ai/chat` root operations; attach LangChain callbacks to SQL generation, SQL correction, RAG answer chain, and verbose list-answer LLM calls; tag traces with `wms-ai`, `sql`, `rag`, route, model, session_id, attempt count, row_count, and source count.

[x] Instrument ExcelAiService: attach LangChain callback config to `PandasQaAgent.ask`; trace `/api/excel/yorumla` only when `soru` triggers the agent; add non-LLM span metadata for deterministic summary/schema flows without logging full dataframe content.

[x] Instrument DocAiService: wrap `OllamaTextClient.chat_json` and `OllamaVlmClient.chat_image_json` with manual `generation` observations; record model, latency, success/error, payload sizes, and sanitized prompt summaries; never send raw image base64 by default.

[x] Add shutdown flushing in FastAPI lifespan hooks so queued Langfuse events are sent cleanly without making Langfuse availability a health-check dependency.

[x] Update docs/env references with Cloud setup steps, region selection, `infra/env/langfuse.local`, masking policy, sampling guidance, and "tracing failure must not fail the request" behavior.

[ ] Validate with tests: disabled mode no-ops, enabled mode passes LangChain callback config, Doc manual observations do not include raw base64, existing service tests still pass, and Langfuse exceptions are swallowed/logged. Partial status: WmsAiService and DocAiService full test suites pass; ExcelAiService Langfuse tests pass, full suite is blocked in the current local Python environment because `pandas` is not installed.

## Validation

- Documentation checks:
  - Confirm self-host is not recommended as an option in this plan.
  - Confirm Cloud endpoint, key, region, masking, sampling, and optional env file steps are explicit.
  - Confirm `infra/env/dev.env` does not contain Langfuse secret values.
- Compose check:
  - `docker compose config` should succeed even when `infra/env/langfuse.local` is absent.
- Implementation checks:
  - `cd WmsAiService && pytest`
  - `cd DocAiService && pytest`
  - `cd ExcelAiService && pytest`
- Current validation notes:
  - `cd WmsAiService && python -B -m pytest -p no:cacheprovider`: 12 passed, 2 skipped.
  - `cd DocAiService && python -B -m pytest -p no:cacheprovider`: 23 passed.
  - `cd ExcelAiService && python -B -m pytest -p no:cacheprovider tests/test_langfuse_tracing.py`: 2 passed.
  - `cd ExcelAiService && python -B -m pytest -p no:cacheprovider`: blocked before running tests because local Python environment is missing `pandas`.
  - `docker compose config`: exits 0; Docker CLI reports a local `C:\Users\Ensar\.docker\config.json` access warning.
- Manual smoke after implementation:
  - Set `LANGFUSE_TRACING_ENABLED=true` and Cloud keys in `infra/env/langfuse.local`.
  - Call WMS chat, Doc extraction, and Excel yorumla with a question.
  - Confirm Langfuse Cloud trace table shows three service-specific traces with nested LLM observations.
  - Confirm Doc VLM traces do not include raw base64 image payloads.
  - Confirm Langfuse network/API failure only logs and does not break service responses.

## Assumptions

- Kullanilacak hedef Langfuse Cloud'dur; self-host bu revizyonda uygulanmayacak.
- Langfuse docs'a gore LangChain entegrasyonu `CallbackHandler` ile yapilir; Cloud credentials `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_BASE_URL` env'leriyle verilir.
- Langfuse SDK batching yaptigi icin servis shutdown sirasinda `flush()` kullanilir.
- Official references used: [LangChain integration](https://langfuse.com/docs/integrations/langchain), [Get Started](https://langfuse.com/docs/observability/get-started), [Environments](https://langfuse.com/docs/observability/features/environments), [Sampling](https://langfuse.com/docs/observability/features/sampling), [Masking](https://langfuse.com/docs/observability/features/masking), [Queuing/Batching](https://langfuse.com/docs/observability/features/queuing-batching), [Pricing](https://langfuse.com/pricing?calculatorOpen=true).
