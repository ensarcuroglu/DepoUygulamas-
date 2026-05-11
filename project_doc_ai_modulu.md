# Doc AI Modulu Hafizasi

Guncel tarih: 2026-05-11

## Servis Siniri

DocAiService, WMS icin belge/irsaliye okuma yapan sibling FastAPI servisidir. Local port `8003` kullanir. Servis DB'ye yazmaz; dosyayi analiz edip taslak JSON ve guven skoru dondurur. Taslak kaydi, inceleme kuyrugu, onay/red ve stok/mal kabul etkileri BackendProje'de authoritative kalir.

## Konfigurasyon

- DocAiService `.env`: `INTERNAL_API_KEY`, `WMS_BASE_URL`, `OLLAMA_BASE_URL`, `OLLAMA_TEXT_MODEL`, `OLLAMA_VLM_MODEL`, `LLM_TIMEOUT`, `MAX_FILE_SIZE_MB`, `CORS_ALLOW_ORIGINS`.
- BackendProje entegrasyonu: `DOC_AI_SERVICE_URL=http://127.0.0.1:8003`, `DOC_AI_SERVICE_TIMEOUT`, `FEATURE_DOC_AI_PILOT_DEPO_IDS`, `INTERNAL_API_KEY`.
- Frontend pilot flag: `VITE_FEATURE_DOC_AI_ENABLED=true`.
- `INTERNAL_API_KEY` BackendProje, DocAiService ve internal HTTP client tarafinda ayni olmalidir.

## Pipeline Notlari

- Text PDF: `TextPdfExtractor` + `OllamaTextClient` + `IrsaliyeTaslagiSchema`.
- Taranmis PDF/JPG: `ImageRenderer` + `OllamaVlmClient`.
- Hibrit karar: `BelgeTipiDedektoru` ve `HibritExtractUseCase`.
- Guven skoru: `confidence_calculator.py`; review queue icin dusuk/orta/yuksek guven ayrimi burada korunur.
- Model degistirmek icin `.env` uzerindeki `OLLAMA_TEXT_MODEL` ve `OLLAMA_VLM_MODEL` yeterlidir. VLM model image input desteklemelidir.

## WMS Entegrasyonu

- Backend upload endpoint'i DocAiService'e internal HTTP ile gider ve `BelgeTaslagi` kaydi olusturur.
- `Idempotency-Key` upload akisi boyunca korunur.
- Inceleme kuyrugu dusuk/orta guven taslaklari listeler; onay/red islemleri BackendProje tarafinda yapilir.

## Degisiklik Kurallari

- Yeni irsaliye alani eklenirse su dosyalar birlikte guncellenir: `DocAiService/app/application/prompts.py`, `DocAiService/app/core/entities/irsaliye_taslagi.py`, few-shot/fixture testleri, `DocAiService/app/core/services/confidence_calculator.py`, Backend DTO/model ve Frontend preview/form alanlari.
- Extraction degisikliginde `pytest tests/test_text_pdf_extraction.py tests/test_vlm_extraction.py tests/test_hibrit_dispatcher.py tests/test_confidence_scoring.py` calistirilir.
- Backend entegrasyonu degisikliginde `INTERNAL_API_KEY`, `X-Internal-Api-Key` ve `Idempotency-Key` sozlesmeleri korunur.

## Komutlar

```powershell
cd DocAiService
pip install -r requirements-test.txt
ollama pull qwen3-vl:4b
uvicorn main:app --reload --host 127.0.0.1 --port 8003
pytest
```

