# ExcelAiService Entegrasyon Plani

> Olusturulma tarihi: 2026-05-14
> Profiller: `/senior-fullstack`, `/langchain-architecture`, `/concise-planning`
> Hedef: WMS'e "AI Destekli Excel Yorumlama" yetenegini, mevcut mikroservis stratejisine sadik kalarak `ExcelAiService` adli bagimsiz bir sibling servis olarak eklemek.

## Yaklasim

DocAiService ile bire bir simetrik bir mikroservis kurgusu uygulanir: ayri Docker servisi, ayri port (`8004`), `INTERNAL_API_KEY` ile korunan dar bir HTTP yuzeyi, **DB yazmaz** (BackendProje authoritative kalir). LangChain tarafinda `pandas DataFrame agent` + Ollama LLM (mevcut `qwen2.5-coder:7b`) kullanilir; ihtiyac durumunda satir/sutun semantik aramasi icin **opsiyonel** ChromaDB koleksiyonu acilir. Excel dosyasi `pandas + openpyxl` ile DataFrame'e cevrilir; soru-cevap, ozetleme ve sema-eslestirme (orn. siparis/stok import on-izleme) gibi use case'ler tek bir orchestration use case altinda toplanir.

## Kapsam

- **In:**
  - `ExcelAiService/` mikroservisi: FastAPI + Clean Architecture (api → application → core / infrastructure) iskeleti.
  - Endpoint'ler: `GET /healthz`, `POST /api/excel/yorumla` (soru-cevap / ozet), `POST /api/excel/sema-esle` (WMS entity mapping onerisi).
  - LangChain pipeline: file → DataFrame → `create_pandas_dataframe_agent` (Ollama) → guard'lanmis cevap.
  - Auth: `X-Internal-Api-Key` middleware + `Idempotency-Key` korumasi (DocAi sozlesmesinin ayni).
  - Docker Compose servisi (`excel-ai`, port `8004`), `infra/env/dev.env` env eklemeleri.
  - BackendProje tarafinda thin HTTP client + 1 router (`/api/excel-ai/*` proxy) + feature flag `FEATURE_EXCEL_AI_ENABLED`.
  - Frontend: tek ekran (Excel upload + soru kutusu + onizleme tablosu), `VITE_FEATURE_EXCEL_AI_ENABLED` flag'i.
  - Pytest iskeleti + happy-path test fixture'lari.
  - Dokumantasyon guncellemeleri: `CLAUDE.md`, `docs/agent/ai-services.md`, `docs/agent/docker-compose.md`, `docs/agent/env-reference.md`.
- **Out:**
  - DB sema degisikligi / Alembic migration. (Persist edilen herhangi bir taslak gerekirse Backend tarafinda `BelgeTaslagi` benzeri ayri bir kayit modeli ile **ikinci** faz.)
  - RabbitMQ event publish. (Excel yorumlama bugun senkron HTTP yeterlidir; outbox/relay hatti faz 2.)
  - Yazilabilir SQL veya WMS aksiyonlari (siparis acma vs.). Servis yalnizca **oneri** doner; aksiyon Backend'de.
  - Production grade scaling / sharding. Tek sureç, tek replika.
  - Cok kullanicili eszamanli buyuk dosya isleme (`MAX_FILE_SIZE_MB` ile sinirli).

## Aksiyon Listesi

[ ] **1. Iskele:** `ExcelAiService/` klasorunu DocAiService simetrisinde olustur (`main.py`, `app/api`, `app/application`, `app/core`, `app/infrastructure`, `tests/`, `requirements.txt`, `requirements-test.txt`, `pytest.ini`, `README.md`).
[ ] **2. Bagimliliklar:** `requirements.txt`'ye `fastapi`, `uvicorn[standard]`, `pydantic-settings`, `httpx`, `pandas`, `openpyxl`, `python-multipart`, `langchain`, `langchain-experimental`, `langchain-ollama`, `tabulate` ekle. Test tarafina `pytest`, `pytest-asyncio`, `httpx[testing]` ekle.
[ ] **3. Config + Auth:** `app/core/config.py` (Settings: `INTERNAL_API_KEY`, `WMS_BASE_URL`, `OLLAMA_BASE_URL`, `OLLAMA_TEXT_MODEL`, `LLM_TIMEOUT`, `MAX_FILE_SIZE_MB`, `MAX_ROWS`, `CORS_ALLOW_ORIGINS`) + `app/api/middleware/auth.py` (`InternalApiKeyMiddleware`, DocAi'dan kopyalanip uyarlanir).
[ ] **4. Dosya katmani:** `app/infrastructure/parsing/excel_loader.py` — `openpyxl`/`pandas.read_excel` ile sayfa listesi + DataFrame; CSV fallback; satir/sutun hard limit (`MAX_ROWS`).
[ ] **5. LLM katmani:** `app/infrastructure/llm/ollama_client.py` (`ChatOllama` factory) + `app/application/agents/pandas_qa_agent.py` (LangChain `create_pandas_dataframe_agent` + sistem promptu Turkce). **Not:** LangChain >=0.3 `create_pandas_dataframe_agent` icin `allow_dangerous_code=True` zorunludur (`PythonAstREPLTool` calistirir). Tehdit modeli `INTERNAL_API_KEY` auth + container izolasyonu + `MAX_ROWS/MAX_FILE_SIZE_MB/max_iterations=8` ile sinirlandirilir. Ek olarak deterministik `summarize_dataframe()` yardimci fonksiyonu LLM cagrisi olmadan template-first ozet uretir.
[ ] **6. Use case'ler:** `ExcelYorumlaUseCase` (soru-cevap + ozet), `ExcelSemaEsleUseCase` (sutun adlari → WMS entity oneri tablosu; sabit hedef sema tanimi `app/core/entities/wms_target_schemas.py`).
[ ] **7. Router'lar:** `app/api/v1/routers/{healthz.py, excel.py}`; multipart upload, `Idempotency-Key`, response model'leri `app/core/entities/responses.py` altinda.
[ ] **8. Docker Compose:** `compose.yml` icine `excel-ai` servisi (port `8004`, `*python-service` anchor, `working_dir=/workspace/ExcelAiService`); `infra/env/dev.env`'ye `EXCEL_AI_SERVICE_URL`, `EXCEL_AI_SERVICE_TIMEOUT`, `FEATURE_EXCEL_AI_ENABLED`, `OLLAMA_TEXT_MODEL` (zaten varsa yeniden kullan).
[ ] **9. Backend entegrasyonu:** `BackendProje/app/infrastructure/clients/excel_ai_client.py` (httpx, `X-Internal-Api-Key`, retry/timeout), `app/api/v1/routers/excel_ai.py` (POST proxy + flag kontrolu), DI `container.py` re-export. **DB yazmaz.**
[ ] **10. Frontend:** `ReactProje/src/pages/ExcelAi/` altinda dropzone + sayfa secimi + soru kutusu + sonuc paneli; `VITE_FEATURE_EXCEL_AI_ENABLED` flag'i; React Query key `["excel-ai", fileHash, soru]`.
[ ] **11. Test:** `ExcelAiService/tests/` icinde (a) auth middleware 401/503, (b) basit XLSX fixture ile happy path (Ollama mock'lu), (c) `MAX_FILE_SIZE_MB`/`MAX_ROWS` limit testleri, (d) sema-esle deterministik testi. `pytest -m unit` ve Backend tarafinda proxy router'i icin httpx mock testi.
[ ] **12. Dokumantasyon:** `CLAUDE.md` (Main Directories + Common Commands + portlar listesi), `docs/agent/ai-services.md` (yeni bolum), `docs/agent/docker-compose.md`, `docs/agent/env-reference.md` guncelle. Bu plan dosyasini `DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md` olarak commit'le.
[ ] **13. Dogrulama:** `docker compose up --build excel-ai backend frontend` ile uctan uca smoke: ornek `siparisler.xlsx` ile (a) `healthz` 200, (b) "Toplam satir kac?" sorusu cevaplanir, (c) sema-esle `siparis_kalemleri` hedefine en az 3 sutun map eder, (d) yanlis API key 503/401.

## Mimari Notlar

- **Klasor yapisi (ozet):**
  ```
  ExcelAiService/
    main.py
    requirements.txt
    requirements-test.txt
    pytest.ini
    README.md
    app/
      api/
        middleware/auth.py
        v1/routers/{healthz.py, excel.py}
      application/
        agents/pandas_qa_agent.py
        use_cases/{excel_yorumla_uc.py, excel_sema_esle_uc.py}
        prompts.py
      core/
        config.py
        entities/{requests.py, responses.py, wms_target_schemas.py}
      infrastructure/
        parsing/excel_loader.py
        llm/ollama_client.py
    tests/
      fixtures/*.xlsx
      test_auth.py
      test_excel_loader.py
      test_pandas_agent.py
      test_router_excel.py
  ```
- **LangChain karari:** Tek dosya/tek soru senaryosunda `create_pandas_dataframe_agent` yeterli; Ollama'nin function-calling zayifligi nedeniyle `agent_type="zero-shot-react-description"` + dar tool seti ile baslanir. Buyuk sayfalarda agent yerine **template-first** ozet (`df.describe()`, `df.head()`, sutun tipleri) + LLM'e yalnizca yorum yaptirilir; bu strateji `WmsAiService.answerer.py`'deki yaklasimla tutarli.
- **Guard'lar:** Pandas DataFrame agent'in calismasi icin `allow_dangerous_code=True` zorunlu (LangChain >=0.3). Risk azaltma katmanlari: (a) servis yalnizca `INTERNAL_API_KEY` ile dahili istemcilere acik, (b) Docker container icinde izole, (c) `MAX_FILE_SIZE_MB/MAX_ROWS/MAX_SHEETS` `ExcelLoader`'da uygulanir, (d) `max_iterations=8` ile zincir uzunlugu sinirlanir, (e) DB / dosya yazma yetkisi yok. Tamamen guvenli "template-first" mod icin `summarize_dataframe()` her zaman uretilir; gerekirse use case agent'i bypass eder.
- **DB / Persistans:** Hicbir kosulda ExcelAiService DB'ye yazmaz. Ileride yuklenen dosyayi saklamak gerekirse BackendProje'de `ExcelTaslagi` entity'si + Alembic migration ile faz 2'de eklenir.
- **Gozlemlenebilirlik:** DocAi pattern'i — structured logging (`logging.basicConfig`), `request_id` korelasyonu Idempotency-Key uzerinden.

## Entegrasyon Noktalari

- **Ollama:** Mevcut `OLLAMA_BASE_URL` ve `OLLAMA_TEXT_MODEL` paylasilir; ek model gerekmez. (`qwen2.5-coder:7b` veya `qwen2.5:7b-instruct`.)
- **BackendProje:** Sadece **proxy + flag**. Authoritative aksiyon yok. Excel'den uretilen "siparis on-izleme" Backend'de mevcut siparis use case'lerine `staged=true` parametresi gerektirmeyecek sekilde sadece response gosterir.
- **Frontend:** Mevcut `apiClient` ve React Query pattern'lerine uyar; ayri sayfa, ayri menu girisi (flag'e bagli).
- **RabbitMQ:** Bu fazda kullanilmaz. Kullanim metrigi gerekirse `lms.event` benzeri bir kanal **faz 2**'de eklenir.
- **AgvSimService / DocAiService:** Bagimlilik yok.

## Risk ve Hafifletme

- **Ollama latency:** Buyuk dosyalarda agent turlarinin uzamasi → `MAX_ROWS=10_000`, `MAX_FILE_SIZE_MB=10`, frontend tarafinda loading + abort.
- **Pandas agent guvenligi:** `allow_dangerous_code=False` zorunlu; CI'da test fixture ile `os`, `subprocess` cagrilarinin blocked oldugu dogrulanir.
- **Turkce sutun adlari:** `pandas_qa_agent` promptunda Turkce ornek few-shot eklenir; column normalization opsiyonel (`unidecode` **eklenmez**, embedding modeli yok).
- **Memory leak (pandas):** Her istek sonu `df` referansi dispose; servis tek sureç, restart toleransli.

## Kararlar (2026-05-14, kullanici onayli)

1. **Mapping hedef semasi:** Ilk surumde **`siparis_kalemleri`, `stok_sayim_kalemleri`, `urun`** desteklenir. `app/core/entities/wms_target_schemas.py` icinde bu uc sema sabit olarak tanimlanir; her birinin alan listesi + alias listesi + zorunlu/opsiyonel isaretleri bulunur.
2. **Frontend konumu:** "AI Asistan" ana menusu altinda yeni alt sekme **"Excel Analizi"** (route: `/ai-asistan/excel`). Mevcut AI Asistan ekranlari ile ayni sidebar grubunda yer alir.
3. **Idempotency anahtari:** `Idempotency-Key = sha256(dosya_icerigi)` **+** `islem_tipi` (`yorumla` | `sema-esle`) **+** kullanici sorusu/hedef sema parametresi. Anahtar uretimi client tarafinda yapilir; server tarafinda 1 saatlik in-memory LRU cache cevabi geri verir. Iki katmanli format: `Idempotency-Key: <sha256-file>:<islem>:<sha256-params>`.

## Dogrulama / Cikis Kriterleri

- `docker compose up --build` sorunsuz; `excel-ai` healthcheck 200.
- `pytest` ExcelAiService dizininde yesil; backend tarafindaki proxy router'i unit testi yesil.
- Manuel smoke (yukaridaki 13 numarali madde) tamamlandi.
- `ruff check .` (ExcelAiService) ve `npm run lint` (ReactProje) temiz.
- Dokumantasyon PR'i ile birlikte (`CLAUDE.md`, `docs/agent/ai-services.md`) merge edilir.
