# AI ve Yardımcı Servisler

Bağımsız yardımcı servisler: WmsAiService (doğal dil → SQL), DocAiService (belge AI), ExcelAiService (Excel yorumlama + WMS şema eşleme), AgvSimService (AGV/AMR simülasyon) ve DataGenService (sentetik veri üretimi).

DataGenService ayrıntıları ayrı runbook'tadır: `DOCS/agent/data-gen-service.md`.

---

## WmsAiService (LangChain + Ollama)

Doğal dil → SQL → read-only execute → cevap. Port: `8001`.

### Komutlar

```bash
cd WmsAiService

pip install -r requirements.txt
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Ollama model (def: qwen2.5-coder:7b)
ollama pull qwen2.5-coder:7b

# DB view'larini olustur (ilk kurulumda bir kez)
mysql -u root -p depo_yonetim < views.sql
```

### Yapı

- `main.py` — FastAPI `/api/ai/*` endpoint'leri.
- `chains.py` — LCEL pipeline: Dinamik Few-Shot SQL üret → çalıştır → self-correct → cevapla.
- `prompts.py` — Sistem promptları, şema açıklaması, statik few-shot örnekleri (fallback, Türkçe).
- `example_selector.py` — Dinamik Few-Shot: ChromaDB + MiniLM-L6-v2 (k=3).
- `ornekler.json` — 40+ soru/SQL çifti (vektör DB kaynağı).
- `answerer.py` — Cevap üretim (template-first; LLM yalnızca `verbose=True`).
- `list_renderer.py` — LIST sonuçlar için deterministik Türkçe template.
- `result_formatter.py` — SCALAR/EMPTY/LIST intent.
- `sql_guard.py` — SELECT-only, whitelist, yasaklı keyword'ler.
- `memory.py` — In-memory session_id LRU+TTL hafıza.
- `views.sql` — 9 read-only MySQL view + `depo_ai_reader` GRANT'ları.
- `wms_chroma_db/` — Persistent ChromaDB (generated).

### Birlesik Chat ve RAG

- `POST /api/ai/chat` tek endpoint akisi slash command, semantic router ve SQL/RAG branch'i birlestirir.
- Yeni WmsAiService modulleri: `vector_config.py`, `slash_commands.py`, `semantic_router.py`, `docs_rag.py`, `chat_orchestrator.py`, `ingest_docs.py`.
- Duz metin sorularda semantic router calisir. `/sql <soru>` Text-to-SQL, `/docs <soru>` dokuman RAG rotasini zorlar.
- RAG cevaplari sadece getirilen dokuman baglamina dayandirilir; baglam yoksa `Bu konuda bilgi bulamadim` doner.
- RAG kaynaklari icin **tek alan**: `DOCS/rag/**/*.md`. CLAUDE.md, `DOCS/agent/**`, README dosyalari ve `DOCKER_DEV.md` operatore donen yanitlarda gozukmemesi icin korpus disinda tutulur. `DOCS/rag/_templates/` altindaki dosyalar sadece sablondur ve indekslenmez.
- Yeni Chroma koleksiyonlari: `wms_ai_router_intents`, `wms_ai_docs_chunks`.
- Markdown chunking `ingest_docs.py` icinde LlamaIndex `MarkdownNodeParser` + `SentenceSplitter` ile yapilir; heading hiyerarsisi korunur ve her chunk govdesinin basina `Title > H2 > H3` breadcrumb eklenir (`breadcrumb` metadata alanina da yazilir). LlamaIndex import edilemezse otomatik olarak eski heading+karakter splitter'a duser. Runtime (Chroma + LangChain) degismez; LlamaIndex sadece ingestion adiminda calisir.

```bash
cd WmsAiService
python ingest_docs.py --all
```

Yeni RAG dokumani eklemek icin `DOCS/rag/_templates/surec-dokumani-template.md` dosyasini `DOCS/rag/<konu>.md` olarak kopyalayip doldur. Dokuman degistikten sonra `python ingest_docs.py --docs` veya router ornekleri de yenilenecekse `python ingest_docs.py --all` calistir.

### Dokuman Yazim Rehberi

- **Tek dosya = tek konu.** Karisik konu retrieval'i bozar.
- **YAML front-matter zorunlu:** `id`, `audience` (operatore donen dokumanlar `operator`), `aliases`, `related`, `updated`, `verified`. `verified: false` ise icerik kod-turevi ve operasyon ekibince dogrulanmamis demektir.
- **Bolum basliklari sablona uymali:** `Amac`, `Kapsam`, `Temel Kurallar`, `Adimlar`, `Istisnalar`, `Dogrulanmasi Gereken Kurallar` (opsiyonel), `Ornek Sorular`, `Kisa Cevap Ozeti`. `ingest_docs.py` heading'e gore boler; bolum adlari section metadata'sina yazilir.
- **Kod blogu kullanmayin** (bash/SQL/python). Embedding'i bozar ve operatore zaten anlamsizdir. Dev dokumantasyonu icin `DOCS/agent/` kullanin (orasi RAG korpusuna girmez).
- **Dogrulanmamis kurallari isaretle:** `> ⚠️ DOĞRULANMASI GEREKEN KURAL` notu + `Dogrulanmasi Gereken Kurallar` bolumu. Ayrica `DOCS/rag/_review/dogrulama-bekliyor.md` dosyasina entity/use case satir referansiyla kaydet.
- **Aliases bolumune es anlamlilari ekle.** "FEFO" ile birlikte "son kullanma onceligi", "SKT onceligi" yazilirsa retrieval kalitesi artar.
- **`_templates/` ve `_review/` underscore prefix tasir.** `ingest_docs.py:iter_source_paths` bunlari atlar.

### Retrieval Kalite Testi

Her doc degisikligi sonrasi:

```bash
cd WmsAiService
python ingest_docs.py --docs
pytest tests/test_rag_retrieval_quality.py -v -s
```

Gold-set `tests/data/rag_goldset.yaml`'da; her doc icin literal+paraphrase+negative sorular vardir. Hedef: **recall@4 >= 0.85**, negatif sorular %100 reddedilmeli (`RAG_STRICT_DISTANCE` esiginin uzerinde olmali). Esige takilirsan dokumana mudahale et (eksik alias, paraphrase, ornek soru); embedding modeli veya prompt'a dokunma.

### Stratejik Notlar

- **Template-first:** Çoğu cevap LLM çağrısı olmadan deterministik şablonla üretilir.
- LLM yalnızca `verbose=True` + LIST intent + validation gate başarılıysa kullanılır.
- Küçük/yerel LLM'lerin Türkçe morfoloji bozukluklarını minimize etmek için.
- **Yeni view eklerken:** `views.sql` + `sql_guard.py` (ALLOWED_TABLES) + `prompts.py` (SCHEMA_DESCRIPTION + FEW_SHOT_EXAMPLES) üçlüsünü birlikte güncelle.
- **Yeni soru/SQL örneği:** `ornekler.json` + ChromaDB yeniden üretimi + `prompts.py` (FEW_SHOT_EXAMPLES fallback) üçlüsünü birlikte güncelle.

---

## DocAiService (Belge AI Mikroservisi)

Irsaliye PDF/JPG → text PDF veya VLM extraction → taslak JSON. Port: `8003`. **DB yazmaz; BackendProje authoritative.**

### Komutlar

```bash
cd DocAiService

pip install -r requirements.txt
pip install -r requirements-test.txt
copy .env.example .env

# Ollama VLM (image input destekleyen model)
ollama pull qwen3-vl:4b

# Dev server
uvicorn main:app --reload --host 127.0.0.1 --port 8003

# Test
pytest
pytest tests/test_confidence_scoring.py

# Health
curl -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8003/healthz
```

### Yapı

- `app/api/v1/routers/{healthz.py, extraction.py}` — public HTTP yüzeyi.
- `app/application/use_cases/{text_pdf_extract_uc.py, hibrit_extract_uc.py}` — orchestration.
- `app/application/prompts.py` — LLM sözleşmesi.
- `app/core/entities/irsaliye_taslagi.py` — şema.
- `app/core/services/confidence_calculator.py` — güven skoru.
- `app/infrastructure/{extraction, llm}` — dosya okuma + Ollama client.

### Auth ve Sınırlar

- `/healthz` ve `/api/extract/irsaliye` dahil tüm non-OPTIONS isteklerde `X-Internal-Api-Key` **zorunlu**; eksik/yanlış/yapılandırılmamışsa bilinçli `503`.
- `Idempotency-Key` yükleme akışında korunur.
- DocAiService DB'ye yazmaz; taslak kaydı + inceleme + onay/red + WMS etkileri BackendProje'de.

### Hibrit Pipeline

- Text PDF (`pdfplumber`) önce; metin yetersizse veya taranmış PDF/JPG ise VLM akışına (`pypdfium2` + Pillow render → Ollama VLM).
- Karar: `BelgeTipiDedektoru` + hibrit dispatcher.
- `OLLAMA_TEXT_MODEL` ve `OLLAMA_VLM_MODEL` env'den; VLM modeli image input desteklemelidir.

### Geliştirme Checklist

- Yeni irsaliye şema alanı: `prompts.py` + `irsaliye_taslagi.py` + few-shot/fixture testleri + `confidence_calculator.py` senkron.
- Extraction değişikliğinde `tests/test_text_pdf_extraction.py`, `tests/test_vlm_extraction.py`, `tests/test_hibrit_dispatcher.py`, `tests/test_confidence_scoring.py` birlikte çalıştır.
- `INTERNAL_API_KEY` / `X-Internal-Api-Key` / `Idempotency-Key` sözleşmesini bozma.

---

## ExcelAiService (Excel Yorumlama + Şema Eşleme Mikroservisi)

Excel/CSV yükle → pandas DataFrame → LangChain `create_pandas_dataframe_agent` (Ollama) ile doğal dil soru/cevap, **veya** sütunları WMS hedef şemalarına (`siparis_kalemleri`, `stok_sayim_kalemleri`, `urun`) eşleme önerisi. Port: `8004`. **DB yazmaz; BackendProje authoritative.**

### Komutlar

```bash
cd ExcelAiService

pip install -r requirements.txt
pip install -r requirements-test.txt
copy .env.example .env

# Mevcut WMS model'i kullanir (code-tuned tercih edilir)
ollama pull qwen2.5-coder:7b

uvicorn main:app --reload --host 127.0.0.1 --port 8004

pytest
pytest -m unit

curl -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8004/healthz
```

### Yapı

- `app/api/middleware/auth.py` — `InternalApiKeyMiddleware` (DocAi sözleşmesinin aynısı).
- `app/api/v1/routers/{healthz.py, excel.py}` — public HTTP yüzeyi.
- `app/application/use_cases/{excel_yorumla_uc.py, excel_sema_esle_uc.py}` — orchestration.
- `app/application/agents/pandas_qa_agent.py` — `create_pandas_dataframe_agent` + `summarize_dataframe` (LLM-siz template-first özet).
- `app/core/entities/wms_target_schemas.py` — Sütun eşleme için hedef şema sabitleri (faz 1: 3 şema, ~27 alan).
- `app/core/services/sema_matcher.py` — Deterministik (LLM-siz) sütun eşleme. Türkçe diakritik normalize + token Jaccard + substring.
- `app/core/services/idempotency_cache.py` — In-memory LRU+TTL.
- `app/infrastructure/parsing/excel_loader.py` — pandas + openpyxl yükleyici, MAX_ROWS/MAX_SHEETS/MAX_FILE_SIZE limit kontrolü, sha256 hash.
- `app/infrastructure/llm/ollama_client.py` — `ChatOllama` factory.

### Endpoint'ler

- `GET /healthz` — internal key + Ollama erişimi + text model varlığı.
- `GET /api/excel/hedef-semalar` — desteklenen WMS şemaları + alan listesi + alias'lar.
- `POST /api/excel/yorumla` — multipart `file` + opsiyonel form `soru`, `sheet_name` → özet + (varsa) agent cevabı.
- `POST /api/excel/sema-esle` — multipart `file` + form `hedef_sema`, opsiyonel `sheet_name` → sütun eşleme + eksik zorunlu alanlar.
- Tüm non-OPTIONS isteklerde `X-Internal-Api-Key` **zorunlu**.

### Auth, Idempotency ve Sınırlar

- Plan: `DOCS/EXCEL_AI_SERVICE_ENTEGRASYON_PLANI.md`.
- `Idempotency-Key` formatı: `sha256(dosya):<islem>:sha256(parametreler)`. Client header göndermezse server kendi hesaplar; LRU+TTL cache (TTL `IDEMPOTENCY_TTL_SECONDS`) ile cevap tekrar verilir.
- Limitler: `MAX_FILE_SIZE_MB=10`, `MAX_ROWS=10000`, `MAX_SHEETS=10`.
- LangChain ≥0.3 `create_pandas_dataframe_agent` için `allow_dangerous_code=True` zorunludur (`PythonAstREPLTool`). Risk azaltma: `INTERNAL_API_KEY` + container izolasyonu + dosya/satır limitleri + `max_iterations=8` + DB/dosya yazma yok.

### Hedef Şemalar (Faz 1)

- `siparis_kalemleri` — zorunlu: `siparis_no`, `urun_kodu`, `miktar` (+ 6 opsiyonel: `urun_adi`, `birim`, `birim_fiyat`, `toplam_fiyat`, `musteri`, `teslim_tarihi`).
- `stok_sayim_kalemleri` — zorunlu: `sayim_no`, `urun_kodu`, `sayim_miktari` (+ `urun_adi`, `lokasyon`, `lot_no`, `sistem_miktari`, `fark`, `sayim_tarihi`).
- `urun` — zorunlu: `urun_kodu`, `urun_adi` (+ `barkod`, `birim`, `agirlik`, `hacim`, `kategori`, `marka`, `aciklama`).
- Yeni şema eklerken: `wms_target_schemas.py` (entity) + `tests/test_sema_matcher.py` (alias coverage testi) + bu doküman birlikte güncellenir.

### Backend Entegrasyonu

- BackendProje proxy: `app/api/v1/routers/excel_ai.py` + `app/infrastructure/services/excel_ai_client.py`. Yalnızca admin guard (`require_role("admin")`) + `FEATURE_EXCEL_AI_ENABLED` flag + `INTERNAL_API_KEY` enjeksiyonu. **Authoritative aksiyon yok**; UI sadece öneri görür.
- Flag kapalıyken `/api/excel-ai/*` 404 döner; flag açıkken `Idempotency-Key` header'ı uçtan uca taşınır.
- Frontend giriş: `/ai-asistan/excel` (AI Asistan menüsü altında "Excel Analizi"), `VITE_FEATURE_EXCEL_AI_ENABLED=true` ile gösterilir.

### Stratejik Notlar

- **Template-first güven:** `summarize_dataframe()` her durumda LLM-siz çalışır (describe + dtypes + head). Soru yoksa agent çağrılmaz.
- **Deterministik şema eşleme:** `sema_matcher` LLM kullanmaz; aynı dosya için tekrarlı çağrı garanti aynı yanıtı döner (test ile doğrulanır).
- **Türkçe normalize:** ı→i, ş→s, ğ→g, ü→u, ö→o, ç→c. Embedding modeli yok — basit deterministik eşleme yeterli.
- Yeni `MAX_*` limit değişikliği: `core/config.py` + healthz response payload + dokümantasyon üçlüsü birlikte.

---

## AgvSimService (AGV/AMR Simülasyon)

In-memory world singleton + asyncio tick loop. Port: `8002`. **DB yok**, restart'ta WMS'ten yeniden senkron.

### Komutlar

```bash
cd AgvSimService

pip install -r requirements.txt
pip install -r requirements-test.txt

uvicorn main:app --reload --host 127.0.0.1 --port 8002

# Test (DB gerekmez, tamamen in-memory)
pytest
```

### Mimari

- FastAPI + asyncio tick loop (`TICK_HZ` Hz).
- Pathfinding: A* + Cooperative-light A* (zaman-uzay `ReservationTable`, vertex+swap conflict, WAIT izni). Deadlock detect: 4 tick replan, 16 tick `HATA_DURUYOR`. Batarya simülasyonu + otonom şarja dönüş.
- Servisler arası: `BackendProje → AGV` HTTP push (görev dispatch). `AGV → BackendProje` HTTP callback (`/api/agv-callbacks/gorev-tamamlandi`). Shared secret: `INTERNAL_API_KEY`.
- WS: `/ws/agv` snapshot + delta + event (frontend Vite proxy üzerinden).

### Sıkı Kurallar

- **Tek süreç zorunlu** — asla replica / multiple worker. `World` in-memory singleton.
- DB yazmaz; AGV restart'ta WMS'ten in-flight görevleri yeniden çekmez (Faz 5'te orphan toleranslı). Dispatcher fire-and-forget — başarısızsa görev WMS'te `Bekliyor` kalır, operatör manuel devralır.
- `X-Internal-Api-Key` her iki yönde zorunlu; key yoksa router'lar `503`.
- Yeni hareket eklerken `app/core/services/rota_planlayici.py` tek nokta; doğrudan `a_star` / `cooperative_a_star` çağırma.
- Frontend HTTPS, AGV plain HTTP/WS. Vite `/ws/agv` ws:true proxy `/api` proxy'sinden ÖNCE.
- Yüksek frekans veri React state'e yazma; useFrame içinde `useAgvStore.getState()` + lerp.
