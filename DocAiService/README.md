# DocAiService

DocAiService, WMS icin irsaliye ve belge okuma yapan FastAPI mikroservisidir. Servis dosyayi analiz eder, normalize edilmis taslak JSON'u ve guven skorlarini dondurur; kalici taslak kaydi, inceleme kuyrugu ve WMS etkileri BackendProje tarafinda kalir.

## Mimari

- `GET /healthz`: internal key ile servis, Ollama erisimi ve text model varligini dogrular.
- `POST /api/extract/irsaliye`: PDF/JPG dosyasini hibrit pipeline ile irsaliye taslagina cevirir.
- Text PDF akisi: `pdfplumber` ile metin cikarimi, Ollama text model, JSON normalize, guven skoru.
- Taranmis PDF/JPG akisi: `pypdfium2` + Pillow render, Ollama VLM model, JSON normalize, guven skoru.
- Dispatcher: text yeterliyse text pipeline, aksi durumda VLM pipeline.
- Auth: `OPTIONS` disindaki isteklerde `X-Internal-Api-Key` zorunludur. Eksik, hatali veya bos konfigurasyon 503 dondurur.

## Kurulum

```powershell
cd DocAiService
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-test.txt
copy .env.example .env
```

`.env` icinde `INTERNAL_API_KEY` degerini BackendProje ile ayni yapin.

## Ollama Modeli

Varsayilan sablonda text ve VLM modeli `qwen3-vl:4b` olarak ayarlanmistir:

```powershell
ollama pull qwen3-vl:4b
```

Modeli istediginiz zaman `.env` uzerinden degistirebilirsiniz:

```env
OLLAMA_TEXT_MODEL=qwen3-vl:4b
OLLAMA_VLM_MODEL=qwen3-vl:4b
```

Taranmis PDF ve JPG icin `OLLAMA_VLM_MODEL` image input destekleyen multimodal bir model olmalidir.

## Calistirma

```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8003
```

Health check:

```powershell
curl.exe -H "X-Internal-Api-Key: <key>" http://127.0.0.1:8003/healthz
```

Manuel extraction denemesi:

```powershell
curl.exe -X POST `
  -H "X-Internal-Api-Key: <key>" `
  -H "Idempotency-Key: manual-doc-ai-1" `
  -F "file=@tests/fixtures/irsaliye_text_pdf.pdf;type=application/pdf" `
  http://127.0.0.1:8003/api/extract/irsaliye
```

## Ortam Degiskenleri

| Degisken | Aciklama |
| --- | --- |
| `INTERNAL_API_KEY` | BackendProje ile paylasilan internal servis anahtari. Zorunlu. |
| `WMS_BASE_URL` | BackendProje adresi. Varsayilan `http://127.0.0.1:8000`. |
| `OLLAMA_BASE_URL` | Ollama API adresi. Varsayilan `http://127.0.0.1:11434`. |
| `OLLAMA_TEXT_MODEL` | Text PDF pipeline icin kullanilan model. |
| `OLLAMA_VLM_MODEL` | Taranmis PDF/JPG pipeline icin kullanilan multimodal model. |
| `LLM_TIMEOUT` | Ollama istek timeout degeri. |
| `MAX_FILE_SIZE_MB` | Kabul edilen dosya boyutu limiti. |
| `CORS_ALLOW_ORIGINS` | Virgulle ayrilmis izinli origin listesi. |

Backend entegrasyonu icin BackendProje tarafinda `DOC_AI_SERVICE_URL`, `DOC_AI_SERVICE_TIMEOUT`, `FEATURE_DOC_AI_PILOT_DEPO_IDS` ve ayni `INTERNAL_API_KEY` degerleri kullanilir.

## Test

```powershell
pytest
pytest tests/test_healthz.py
pytest tests/test_text_pdf_extraction.py tests/test_vlm_extraction.py tests/test_hibrit_dispatcher.py tests/test_confidence_scoring.py
```

`pytest.ini` marker'lari: `unit`, `integration`, `extraction`.

## Sorun Giderme

- `/healthz` 503 donuyorsa `INTERNAL_API_KEY`, header adi ve Ollama model varligini kontrol edin.
- Health response model yok diyorsa `ollama pull <model>` calistirin ve `OLLAMA_TEXT_MODEL` degerini kontrol edin.
- Taranmis PDF text pipeline'da bos geliyorsa bu beklenen durumdur; dispatcher VLM pipeline'a dusmelidir.
- JPG/taranmis PDF hatalarinda `pypdfium2` ve Pillow kurulumunu, dosya tipini ve `MAX_FILE_SIZE_MB` limitini kontrol edin.
- VLM cok yavas ise daha kucuk bir multimodal model secin veya `LLM_TIMEOUT` degerini artirin.
- Frontend CORS hatalarinda `CORS_ALLOW_ORIGINS=https://localhost:5173` degerini ve Vite HTTPS origin'ini kontrol edin.
- Backend upload akisi gorunmuyorsa `FEATURE_DOC_AI_PILOT_DEPO_IDS` ve `VITE_FEATURE_DOC_AI_ENABLED=true` ayarlarini kontrol edin.

