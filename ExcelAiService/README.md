# ExcelAiService

ExcelAiService, WMS icin Excel/CSV dosyalarini yorumlayan FastAPI mikroservisidir. Dosyayi pandas ile yukler, LangChain `pandas DataFrame agent` (Ollama LLM) uzerinden dogal dil sorulari cevaplar ve WMS hedef semalarina ("siparis_kalemleri", "stok_sayim_kalemleri", "urun") sutun esleme onerisi uretir.

> **Servis DB'ye yazmaz.** Authoritative kayit ve aksiyon BackendProje tarafindadir; ExcelAiService yalnizca senkron HTTP yanit doner.

## Yapi

- `app/api/middleware/auth.py` — `InternalApiKeyMiddleware` (DocAi sozlesmesinin aynisi).
- `app/api/v1/routers/{healthz.py, excel.py}` — HTTP yuzeyi.
- `app/application/use_cases/` — `ExcelYorumlaUseCase`, `ExcelSemaEsleUseCase`.
- `app/application/agents/pandas_qa_agent.py` — LangChain agent.
- `app/core/entities/wms_target_schemas.py` — Hedef sema sabitleri.
- `app/infrastructure/parsing/excel_loader.py` — pandas + openpyxl yukleyici.
- `app/infrastructure/llm/ollama_client.py` — Ollama text client.

## Endpoint'ler (planlanan)

- `GET /healthz` — internal key + Ollama erisimi + text model varligi.
- `POST /api/excel/yorumla` — multipart upload + soru → cevap + ozet.
- `POST /api/excel/sema-esle` — multipart upload + hedef sema adi → sutun esleme onerisi.

Tum non-OPTIONS isteklerde `X-Internal-Api-Key` zorunludur.

## Idempotency

`Idempotency-Key = sha256(dosya):<islem>:sha256(parametreler)` formati. Server tarafinda in-memory LRU cache ile cevap tekrari verilir (TTL `IDEMPOTENCY_TTL_SECONDS`).

## Kurulum

```powershell
cd ExcelAiService
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-test.txt
copy .env.example .env
```

`.env` icinde `INTERNAL_API_KEY` degerini BackendProje ile ayni yapin.

## Calistirma

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8004
```

Health check:

```powershell
curl.exe -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8004/healthz
```

## Test

```powershell
pytest
pytest -m unit
pytest -m excel
```

## Ortam Degiskenleri

| Degisken | Aciklama |
| --- | --- |
| `INTERNAL_API_KEY` | BackendProje ile paylasilan internal servis anahtari. Zorunlu. |
| `WMS_BASE_URL` | BackendProje adresi. Varsayilan `http://127.0.0.1:8000`. |
| `OLLAMA_BASE_URL` | Ollama API adresi. Varsayilan `http://127.0.0.1:11434`. |
| `OLLAMA_TEXT_MODEL` | LangChain pandas agent icin kullanilan model. |
| `LLM_TIMEOUT` | Ollama istek timeout degeri (saniye). |
| `MAX_FILE_SIZE_MB` | Kabul edilen dosya boyutu limiti. |
| `MAX_ROWS` | Tek sayfada okunan maksimum satir sayisi. |
| `MAX_SHEETS` | Kabul edilen maksimum sayfa sayisi. |
| `IDEMPOTENCY_TTL_SECONDS` | Idempotency cache TTL (saniye). |
| `IDEMPOTENCY_MAX_ENTRIES` | Idempotency cache max entry. |
| `CORS_ALLOW_ORIGINS` | Virgulle ayrilmis izinli origin listesi. |

Backend entegrasyonu icin BackendProje tarafinda `EXCEL_AI_SERVICE_URL`, `EXCEL_AI_SERVICE_TIMEOUT`, `FEATURE_EXCEL_AI_ENABLED` ve ayni `INTERNAL_API_KEY` degerleri kullanilir.

## Plan Referansi

Tam entegrasyon plani: `DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md`.
