# DocAiService — Implementation Plan

## Approach

Yeni `DocAiService` (port **8003**), fiziksel depo belgelerini (irsaliye/fatura, PDF veya görüntü) yapılandırılmış JSON'a çeviren bağımsız bir mikroservistir. Hibrit pipeline kullanır: text-tabanlı PDF için `pdfplumber` + LLM (qwen2.5:7b), taranmış PDF/JPG/PNG için VLM (qwen2.5-vl:7b veya minicpm-v:8b). Çıktı, `BackendProje`'de `BelgeTaslagi` (KABUL_BEKLIYOR) olarak kaydedilir; depocu mobil terminal/dashboard üzerinden taslağı görsel doğrulayıp onaylar — manuel veri girişi sıfıra iner. Mimari `WmsAiService` (LangChain/Ollama deseni) ve `AgvSimService` (sibling FastAPI + INTERNAL_API_KEY deseni) üzerine inşa edilir.

## Scope

- **In:**
  - `DocAiService/` sibling FastAPI servisi (Clean Architecture: `app/core`, `app/application`, `app/infrastructure`, `app/api`)
  - Hibrit extraction pipeline (pdfplumber dispatcher + Ollama text LLM + Ollama VLM)
  - Pydantic şema doğrulama + alan-bazlı `confidence_score`
  - WMS entegrasyon: `BelgeTaslagi` entity + tablo + alembic migration + `/api/belge-taslaklari/*` router
  - Frontend: Dashboard upload sayfası + Mobil terminal kamera capture
  - Mal kabul önizleme/onay ekranı (alan-bazlı edit + tek tıkla `MalKabulIrsaliye` oluştur)
  - INTERNAL_API_KEY ikili auth, Idempotency-Key, Feature flag (`FEATURE_DOC_AI_PILOT_DEPO_IDS`)
  - Low-confidence taslakları için manuel inceleme kuyruğu

- **Out:**
  - Bulut LLM (Anthropic/OpenAI) entegrasyonu
  - ERP/email otomatik dinleme (Faz 7+ ileri sürüm)
  - Çoklu dil desteği (sadece Türkçe belgeler)
  - Belge sınıflandırma ML (irsaliye vs fatura — kullanıcı seçer)
  - Replica/cluster çalıştırma (DocAi tek süreçte yeterli; stateless ama tek instance)
  - Veri girişi yapan veritabanı erişimi DocAi'den (yazma sadece WMS üzerinden callback)

---

## Action Items

### Faz 0 — Servis İskeleti & Auth (1 gün)

- [ ] `DocAiService/` dizinini oluştur (sibling: `BackendProje`, `WmsAiService` ile aynı seviye)
- [ ] `DocAiService/main.py` — FastAPI app, CORS, lifespan, `/healthz` endpoint
- [ ] `DocAiService/requirements.txt` — fastapi, uvicorn, pydantic, pydantic-settings, httpx, pdfplumber, pillow, ollama, python-multipart
- [ ] `DocAiService/requirements-test.txt` — pytest, pytest-asyncio, httpx
- [ ] `DocAiService/.env.example` — `INTERNAL_API_KEY`, `WMS_BASE_URL=http://127.0.0.1:8000`, `OLLAMA_BASE_URL`, `OLLAMA_TEXT_MODEL=qwen2.5:7b`, `OLLAMA_VLM_MODEL=qwen2.5-vl:7b`, `LLM_TIMEOUT=120`, `MAX_FILE_SIZE_MB=25`, `CORS_ALLOW_ORIGINS=https://localhost:5173`
- [ ] `DocAiService/app/core/config.py` — pydantic-settings tabanlı `Settings` (BackendProje deseni)
- [ ] `DocAiService/app/api/middleware/auth.py` — `X-Internal-Api-Key` zorunlu middleware (AgvSimService deseni); 401 yerine 503 döner
- [ ] `DocAiService/app/api/v1/routers/healthz.py` — `/healthz` (Ollama bağlantı + model varlık kontrolü)
- [ ] `DocAiService/pytest.ini` — marker'lar (`unit`, `integration`, `extraction`)
- [ ] `DocAiService/tests/test_healthz.py` — 200 + auth header eksikse 503
- [ ] **Validation:** `uvicorn main:app --port 8003` başlat, `curl -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8003/healthz` → 200

### Faz 1 — Text PDF Pipeline (2 gün)

- [ ] `DocAiService/app/core/entities/belge.py` — `Belge`, `BelgeAlani`, `ExtractionSonucu` dataclass'ları
- [ ] `DocAiService/app/core/entities/irsaliye_taslagi.py` — Pydantic `IrsaliyeTaslagiSchema` (tedarikçi, irsaliye_no, tarih, kalemler[urun_kodu, ad, miktar, birim], toplam) + alan başına `confidence: float`
- [ ] `DocAiService/app/core/services/belge_tipi_dedektoru.py` — `pdfplumber` ile metin var mı? → `TEXT_PDF` / `SCANNED_PDF` / `IMAGE`
- [ ] `DocAiService/app/infrastructure/llm/ollama_text_client.py` — httpx tabanlı Ollama `/api/chat` çağrısı (JSON mode, temperature=0)
- [ ] `DocAiService/app/infrastructure/extraction/text_pdf_extractor.py` — pdfplumber → ham metin → Ollama text LLM → Pydantic parse
- [ ] `DocAiService/app/application/prompts.py` — sistem promptu (Türkçe, irsaliye şeması açıklaması) + `FEW_SHOT_EXAMPLES` (3-5 gerçek irsaliye örneği)
- [ ] `DocAiService/app/application/use_cases/text_pdf_extract_uc.py` — orchestration: dosya bytes → extractor → schema → confidence
- [ ] `DocAiService/app/api/v1/routers/extraction.py` — `POST /api/extract/irsaliye` (multipart, Idempotency-Key destekli)
- [ ] `DocAiService/tests/fixtures/irsaliye_text_pdf.pdf` — gerçek örnek belge
- [ ] `DocAiService/tests/test_text_pdf_extraction.py` — şema doğrulama, en az 3 alanın `confidence > 0.7`
- [ ] **Validation:** Örnek text PDF post et → 200 + JSON şema + tüm zorunlu alanlar dolu

### Faz 2 — VLM Pipeline & Hibrit Dispatcher (2-3 gün)

- [ ] `ollama pull qwen2.5-vl:7b` (alternatif: `minicpm-v:8b` — daha küçük VRAM)
- [ ] `DocAiService/app/infrastructure/llm/ollama_vlm_client.py` — base64 image + prompt → Ollama `/api/chat` (multimodal)
- [ ] `DocAiService/app/infrastructure/extraction/image_renderer.py` — `pdf2image` veya `pypdfium2` ile PDF sayfa → PIL Image
- [ ] `DocAiService/app/infrastructure/extraction/vlm_extractor.py` — image → VLM → JSON parse
- [ ] `DocAiService/app/application/use_cases/hibrit_extract_uc.py` — dispatcher: `belge_tipi_dedektoru` → text/vlm extractor seçimi
- [ ] `DocAiService/app/application/prompts.py` — `VLM_IRSALIYE_PROMPT` (görsel layout odaklı, "tablo halinde kalemleri oku" yönergesi)
- [ ] `extraction.py` router'ında `/api/extract/irsaliye` endpoint'i hibrit dispatcher'a bağla
- [ ] `DocAiService/tests/fixtures/irsaliye_scanned.jpg`, `irsaliye_scanned.pdf`
- [ ] `DocAiService/tests/test_vlm_extraction.py` (marker: `extraction`, slow)
- [ ] `DocAiService/tests/test_hibrit_dispatcher.py` — text PDF → text path, scanned → vlm path
- [ ] **Validation:** 3 örnek (text PDF, scanned PDF, JPG) → her biri >0.6 ortalama confidence

### Faz 3 — WMS Entegrasyonu (2 gün)

- [ ] `BackendProje/models.py` → `BelgeTaslagi` ORM modeli (id, kaynak_dosya_yolu, belge_tipi, ham_json, durum [TASLAK/KABUL_EDILDI/REDDEDILDI], confidence_skoru, olusturan_kullanici_id, depo_id, mal_kabul_irsaliye_id [nullable], created_at)
- [ ] `BackendProje/app/core/entities/belge_taslagi.py` — domain entity dataclass
- [ ] `BackendProje/app/core/repositories/belge_taslagi_repository.py` — abstract interface
- [ ] `BackendProje/app/infrastructure/persistence/repositories/belge_taslagi_repository_impl.py`
- [ ] `BackendProje/app/infrastructure/persistence/mappers/belge_taslagi_mapper.py`
- [ ] `BackendProje/app/application/use_cases/belge_taslagi_use_cases.py` — `OlusturBelgeTaslagiUC`, `ListeleBelgeTaslagiUC`, `OnaylaBelgeTaslagiUC` (taslak → MalKabulIrsaliye dönüşümü), `ReddetBelgeTaslagiUC`
- [ ] `BackendProje/app/application/dto/belge_taslagi_dto.py`
- [ ] `BackendProje/app/infrastructure/di/modules/belge_taslagi.py` — DI factory'leri
- [ ] `BackendProje/app/infrastructure/di/container.py` → re-export
- [ ] `BackendProje/app/api/v1/routers/belge_taslaklari.py` — `POST /api/belge-taslaklari/` (DocAi callback, INTERNAL_API_KEY ile), `GET /api/belge-taslaklari/`, `GET /{id}`, `POST /{id}/onayla`, `POST /{id}/reddet`
- [ ] `BackendProje/main.py` → router kayıt
- [ ] `BackendProje/alembic/versions/<hash>_belge_taslaklari_tablosu.py` — migration
- [ ] `alembic upgrade head` (drift kontrolü için zorunlu)
- [ ] `BackendProje/app/core/config.py` → `FEATURE_DOC_AI_PILOT_DEPO_IDS`, `DOC_AI_SERVICE_URL=http://127.0.0.1:8003`, `DOC_AI_SERVICE_TIMEOUT=120`
- [ ] `BackendProje/app/infrastructure/services/doc_ai_client.py` — DocAi'ye dosya gönderme client'ı (httpx, INTERNAL_API_KEY)
- [ ] `BackendProje/app/api/v1/routers/mal_kabul.py` → `POST /api/mal-kabul/belge-yukle` (depo flag kontrol → DocAi'ye proxy → taslak yarat)
- [ ] `BackendProje/tests/integration/test_belge_taslagi_e2e.py`
- [ ] **Validation:** Frontend'ten dosya yükle → BelgeTaslagi DB'de oluşur → DocAi extraction çıktısı `ham_json`'da → onayla butonu → `MalKabulIrsaliye` kaydı oluşur

### Faz 4 — Dashboard Upload & Önizleme (2 gün)

- [ ] `ReactProje/src/services/belgeTaslagiApi.js` — endpoint fonksiyonları
- [ ] `ReactProje/src/queries/belgeTaslagiQueries.js` + `queryKeys.js` → `belgeTaslaklari` namespace
- [ ] `ReactProje/src/pages/MalKabul/BelgeYuklePage.jsx` — drag-drop + dosya seçici, depo seçimi, yükleme progress
- [ ] `ReactProje/src/pages/MalKabul/BelgeTaslagiOnizlemePage.jsx` — sol: belge önizleme (PDF.js / `<img>`), sağ: alan-bazlı form (her input yanında confidence rozeti)
- [ ] `ReactProje/src/components/belge/AlanGuvenRozeti.jsx` — yeşil/sarı/kırmızı (>0.85, 0.5-0.85, <0.5)
- [ ] `ReactProje/src/components/belge/KalemTablosu.jsx` — düzenlenebilir tablo (satır ekle/sil, ürün kodu autocomplete)
- [ ] `ReactProje/src/App.jsx` → `/mal-kabul/belge-yukle`, `/mal-kabul/taslak/:id` route'ları (RoleRoute: admin/lojistik/depocu)
- [ ] Sidebar item ekle (sadece `VITE_FEATURE_DOC_AI_ENABLED=true` ise)
- [ ] **Validation:** Web'den irsaliye yükle → önizleme açılır → 1-2 alan düzelt → onayla → toast "Mal kabul oluşturuldu" + redirect

### Faz 5 — Mobil Terminal Kamera Capture (1-2 gün)

- [ ] `ReactProje/src/hooks/useDocumentCapture.js` — getUserMedia (environment cam), shutter, blob döndür
- [ ] `ReactProje/src/components/terminal/BelgeKameraOverlay.jsx` — full-screen kamera + çerçeve overlay + çek butonu
- [ ] `ReactProje/src/utils/imageCropper.js` — basit auto-crop (kenar tespit; gerekirse `opencv.js` opsiyonel — yoksa manuel crop fallback)
- [ ] `ReactProje/src/pages/terminal/BelgeFotograflaPage.jsx` — çek → önizle → "Yükle ve İşle" → onizleme sayfasına yönlendir
- [ ] `ReactProje/src/App.jsx` → `/terminal/belge-fotografla` (TerminalLayout, RoleRoute: depocu)
- [ ] Terminal ana menüsüne "Belge Çek" butonu
- [ ] **Validation:** Telefon Chrome'da PWA aç → kamera çalışır → fotoğraf çek → upload başarılı → taslak ekranı

### Faz 6 — Güven Skoru, Test, İnceleme Kuyruğu (1-2 gün)

- [ ] `BackendProje/app/api/v1/routers/belge_taslaklari.py` → `GET /api/belge-taslaklari/inceleme-kuyrugu` (confidence < 0.6 olanlar, admin/lojistik)
- [ ] `ReactProje/src/pages/admin/BelgeIncelemeKuyruguPage.jsx`
- [ ] `DocAiService/app/core/services/confidence_calculator.py` — alan-bazlı + ortalama hesabı + missing_fields listesi
- [ ] Boş/eksik alanlarda `confidence: 0.0` + `validation_errors[]` döndür
- [ ] `BackendProje/tests/api/routers/test_belge_taslaklari.py` — auth, role, idempotency, callback flow
- [ ] `DocAiService/tests/test_confidence_scoring.py`
- [ ] `BackendProje/tests/integration/test_doc_ai_e2e.py` — gerçek text PDF + mock DocAi → MalKabul oluşturma
- [ ] `ruff check .` (BackendProje + DocAiService)
- [ ] `pytest -m unit` BackendProje
- [ ] `pytest` DocAiService
- [ ] `npm run lint` ReactProje
- [ ] **Validation:** `pytest --cov=app` DocAiService → unit testlerde >70% coverage; E2E testte 1 belge end-to-end yeşil

### Faz 7 — CLAUDE.md & Dokümantasyon

- [ ] `CLAUDE.md` → DocAiService bölümü (yapı, env, port 8003, çalıştırma komutu, hibrit pipeline notu)
- [ ] `CLAUDE.md` → "AI Agent Development Checklist" → DocAiService değişiklikleri için yeni kalemler (yeni şema alanı eklerken `prompts.py` + `IrsaliyeTaslagiSchema` + few-shot üçlüsü senkron)
- [ ] `DocAiService/README.md` — kurulum, model çekme komutları, troubleshooting
- [ ] `auto memory` → `project_doc_ai_modulu.md` ekle, `MEMORY.md` index'e referans

---

## Validation (Genel Kabul Kriterleri)

- `DocAiService` 8003'te ayağa kalkar; `/healthz` Ollama+model durumunu doğrular
- Text PDF: 5/5 örnek belgede zorunlu alanlar (tedarikçi, irsaliye_no, tarih, en az 1 kalem) > 0.8 confidence
- Scanned PDF/JPG: 4/5 örnek belgede aynı alanlar > 0.6 confidence
- Backend → DocAi → callback → BelgeTaslagi → onay → MalKabulIrsaliye end-to-end < 30 saniye (text PDF için)
- Idempotency-Key tekrar yükleme aynı taslağı döner (yeni kayıt yaratmaz)
- Feature flag kapalıysa `/api/mal-kabul/belge-yukle` 404/403 döner
- INTERNAL_API_KEY eksikse her iki yönde 503
- Ruff + pyright + pytest + ESLint temiz

---

## Open Questions

1. **VLM model seçimi kesin mi?** — qwen2.5-vl:7b VRAM ihtiyacı (~5GB). Eğer GPU yoksa CPU'da 30-60s/belge çok yavaş; minicpm-v:8b daha verimli ama Türkçe kalitesi test edilmeli. Faz 2 başında 2 model üzerinde 5 örnekle benchmark yapılmalı.
2. **Belge depolama:** Yüklenen orijinal dosya nerede saklanacak? `BackendProje/uploads/belge_taslaklari/<id>/` mı, S3/MinIO mu? Plan şu an local filesystem varsayıyor (mevcut `uploads/` deseni). Production için ayrıştırma gerekebilir.
3. **Ürün kodu eşleştirme:** Tedarikçi belgesindeki ürün kodu WMS `urun_kodu` ile birebir eşleşmiyorsa? Faz 6'da fuzzy match (rapidfuzz) + manuel eşleştirme UI'ı eklenmeli mi yoksa ayrı bir Faz 8 mi olsun?
