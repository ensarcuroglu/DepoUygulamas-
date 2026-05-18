# AssistantAiService

Kullanici/rol baglamina sahip, insan onayli aksiyon (Human-in-the-Loop) yapabilen depo asistani mikroservisi. WMS ekosisteminde **port 8006** uzerinde calisir.

Bu servis **DB'ye dokunmaz**. Authoritative tum yazimlar `BackendProje` uzerinden gerceklesir; AssistantAiService sadece LLM orkestrasyonu yapar ve onerilen aksiyonlari (`ProposedAction`) Backend'in onay endpoint'ine doner.

## Mimari

Mimari kararlar, faz plani ve dizin agaci tek dokumanda toplandi:

- [DOCS/ASSISTANT_AI_SERVICE_ENTEGRASYON_PLANI.md](../DOCS/ASSISTANT_AI_SERVICE_ENTEGRASYON_PLANI.md)

ExcelAiService / DocAiService kardesleriyle ayni Clean Architecture katmanlamasini kullanir:

```text
app/
|-- api/           HTTP concerns (routers, middleware)
|-- application/   Use case orchestration, agent graph (Faz 2)
|-- core/          Settings, entities, domain services
`-- infrastructure/ LLM client, checkpointer, backend client (Faz 2)
```

## Calistirma

Compose stack icinden onerilen yol:

```bash
docker compose up -d --build assistant-ai
```

Lokal manuel calistirma:

```bash
cd AssistantAiService
pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8006
```

Health check:

```bash
curl -H "X-Internal-Api-Key: <key>" http://localhost:8006/healthz
```

## Chat sozlesmesi

BackendProje, `POST /api/asistan/chat` endpoint'ini internal API key ile
cagirir. Bu endpoint su anda sozlesmeyi ve session davranisini garanti eder;
LangGraph/tool orkestrasyonu devreye girene kadar `proposed_action=null`
doner.

## Env Degiskenleri

| Degisken | Aciklama | Varsayilan |
|---|---|---|
| `INTERNAL_API_KEY` | Backend ile paylasilan shared secret (zorunlu) | yok |
| `OLLAMA_BASE_URL` | Ollama API endpoint'i | `http://127.0.0.1:11434` |
| `ASSISTANT_LLM_MODEL` | LangChain ChatOllama icin model adi | `qwen2.5-coder:7b` |
| `LLM_TIMEOUT` | Ollama HTTP timeout (saniye) | `120` |
| `BACKEND_BASE_URL` | BackendProje base URL'i (read-only tool'lar icin Faz 2) | `http://127.0.0.1:8000` |
| `SQLITE_CHECKPOINT_PATH` | LangGraph SqliteSaver dosya yolu (Faz 2) | `/data/assistant_state.sqlite` |
| `CORS_ALLOW_ORIGINS` | Virgulle ayrilmis izinli origin listesi | `https://localhost:5173` |

## Faz Plani

| Faz | Icerik | Durum |
|---|---|---|
| 0 | Iskelet (paket, config, healthz, middleware, compose, env) | tamam |
| 1 | Backend authoritative katman + AssistantAiService chat sozlesmesi | **bu PR** |
| 2 | AssistantAiService cekirdek (LangGraph, tools, chat endpoint, SqliteSaver) | sonraki |
| 3 | Frontend `/depo-asistani` sayfasi | sonraki |
| 4 | Dokumantasyon + smoke test | sonraki |

## Kisitlar

- **Tek replica:** AgvSimService gibi `assistant-ai` da tek surec calismalidir (SqliteSaver dosya kilidi).
- **DB'ye dokunmaz:** Tum yazimlar BackendProje uzerinden gider.
- **JWT dogrulamaz:** Auth Backend'de yapilir; servis sadece `X-Internal-Api-Key` ile korunur.
