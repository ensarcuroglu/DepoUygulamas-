# AI ve Yardımcı Servisler

Üç bağımsız mikroservis: WmsAiService (doğal dil → SQL), DocAiService (belge AI), AgvSimService (AGV/AMR simülasyon).

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
- RAG kaynaklari icin ozel alan: `DOCS/rag/**/*.md`. `DOCS/rag/_templates/` altindaki dosyalar sadece sablondur ve indekslenmez.
- Yeni Chroma koleksiyonlari: `wms_ai_router_intents`, `wms_ai_docs_chunks`.

```bash
cd WmsAiService
python ingest_docs.py --all
```

Yeni RAG dokumani eklemek icin `DOCS/rag/_templates/surec-dokumani-template.md` dosyasini `DOCS/rag/<konu>.md` olarak kopyalayip doldur. Dokuman degistikten sonra `python ingest_docs.py --docs` veya router ornekleri de yenilenecekse `python ingest_docs.py --all` calistir.

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
