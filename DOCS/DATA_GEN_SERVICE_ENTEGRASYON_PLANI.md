# DataGenService — Sentetik Depo Veri Üreticisi Entegrasyon Planı

## Amaç

WMS ekosistemini test etmek, sınırlarını zorlamak ve `ml_models/talep_tahmin/` altındaki ML modellerini eğitmek için gerçeğe yakın, ilişkisel bütünlüğü korunmuş hacimli dummy veri üreten bağımsız bir mikroservis (+ CLI). Mevcut `DocAiService` / `ExcelAiService` deseninde kurgulanır; veritabanına doğrudan yazmaz, yalnızca **Backend REST API** veya **`depo.events`** RabbitMQ exchange'i üzerinden sisteme veri besler.

## Yüksek Seviye Yaklaşım

- Bağımsız servis: `DataGenService/` (FastAPI + Typer CLI), port **8005**.
- Yazma yolu: Backend uçları (`X-Internal-Api-Key` + `Idempotency-Key`) veya RabbitMQ publisher (`depo.events`, persistent + confirm). Backend'in iş kuralları / state transition'ları by-pass edilmez.
- Throttle: `asyncio.Semaphore(CONCURRENCY=10)` + `BATCH_SIZE=500` (HTTPX async), exponential backoff retry.
- ML zaman serisi: varsayılan olarak dosya (`ml_models/talep_tahmin/data/raw/*.parquet`); `--target=rest` opsiyonel.
- AGV trafik senaryosu: yalnız Backend yerleştirme/toplama uçları üzerinden; **AgvSimService'e doğrudan çağrı yapılmaz** (WMS state bütünlüğü korunur).

## Kapsam

### Dahil

- `DataGenService/` mikroservisi, `Dockerfile`, `compose.yml` servis kaydı, `infra/env/dev.env` değişkenleri.
- Pydantic DTO çıktı veren factory katmanı (Faker / Mimesis + factory-boy), deterministik seed, ilişkisel bütünlük (referans havuzu → bağımlılar).
- 4 senaryo: `seed_baseline`, `task_load`, `timeseries_history`, `agv_traffic`.
- `IEmitter` protokolü altında `rest_emitter`, `rabbit_emitter`, `file_emitter`.
- `--target={rest,rabbit,file}` parametresi + senaryo başına izinli hedef matrisi.
- Pytest unit smoke testleri (`-m unit`), `/healthz` endpoint, JSON özet rapor (toplam / başarı / hata / p95 latency).

### Dahil Değil

- Backend şema, use case veya migration değişikliği.
- Frontend (`ReactProje/`) değişikliği.
- AgvSimService'e doğrudan trafik enjeksiyonu (kararlı: kapsam dışı).
- Prod hedefli kimlik / yetkilendirme akışı (yalnız dev / staging).

## Teknoloji Yığını

| Bileşen | Amaç |
|---|---|
| **FastAPI** | `/healthz`, `/scenarios/{name}/run` HTTP yüzeyi |
| **Typer** | `python -m datagen run <scenario>` CLI |
| **Faker / Mimesis** | Gerçekçi isim, adres, şirket, ürün kodu, barkod (`LOCALE=tr_TR`) |
| **factory-boy** | Senaryo bazlı, deterministik DTO factory'leri |
| **Pydantic / pydantic-settings** | Şema validasyonu + ortam değişkeni yönetimi |
| **HTTPX (AsyncClient)** | Asenkron REST yayını, retry, idempotency |
| **aio-pika** | RabbitMQ publisher (persistent + confirm + mandatory) |
| **pandas + pyarrow** | ML eğitim verisi (CSV / Parquet) çıktısı |

## Karar Notları

1. **Hacim & rate-limit:** MVP hedefi ~1.000 ürün + ~10.000 palet. İstekler `BATCH_SIZE=500` paketlerinde, `Semaphore(10)` eşzamanlılığıyla atılır. Default backoff: `0.5s → 1s → 2s → 4s`, max 3 retry.
2. **`timeseries_history` çıktı hedefi:** Çift modlu. **Varsayılan `--target=file`** → `ml_models/talep_tahmin/data/raw/talep_gecmis_{tarih}.parquet`. `--target=rest` yalnız opsiyonel; WMS DB'sini geçmiş veriyle şişirmemek için tercih edilmez.
3. **AGV trafik bağlantısı:** `agv_traffic` senaryosu **yalnızca `target=rest`** olarak Backend yerleştirme / toplama uçlarına bağlanır. WMS, kendi akışı üzerinden AGV'yi tetikler. AgvSimService doğrudan çağrılmaz.

## Hedef İzin Matrisi (Senaryo × Target)

| Senaryo | `rest` | `rabbit` | `file` |
|---|:---:|:---:|:---:|
| `seed_baseline` | ✅ (default) | ❌ | ❌ |
| `task_load` | ✅ | ✅ | ❌ |
| `timeseries_history` | ✅ (opt) | ❌ | ✅ (default) |
| `agv_traffic` | ✅ (only) | ❌ | ❌ |

İzinsiz `target` kombinasyonu API'de `422 Unprocessable Entity` ile reddedilir.

## Klasör Yapısı (Hedef)

```
DataGenService/
├── main.py                       # FastAPI app + /healthz + /scenarios/{name}/run
├── cli.py                        # Typer entrypoint (python -m datagen run ...)
├── requirements.txt
├── Dockerfile
├── README.md
├── app/
│   ├── core/
│   │   └── config.py             # pydantic-settings
│   ├── factories/                # Pydantic DTO döndüren factory'ler
│   │   ├── urun_factory.py
│   │   ├── raf_factory.py
│   │   ├── palet_factory.py
│   │   ├── lot_factory.py
│   │   ├── siparis_factory.py
│   │   ├── yerlestirme_gorev_factory.py
│   │   ├── toplama_gorev_factory.py
│   │   └── talep_zaman_serisi_factory.py
│   ├── infrastructure/
│   │   └── emitters/
│   │       ├── base.py           # IEmitter Protocol
│   │       ├── rest_emitter.py   # HTTPX async + Semaphore + retry
│   │       ├── rabbit_emitter.py # aio-pika confirm + persistent
│   │       └── file_emitter.py   # pyarrow CSV/Parquet
│   └── scenarios/
│       ├── seed_baseline.py
│       ├── task_load.py
│       ├── timeseries_history.py
│       └── agv_traffic.py
└── tests/
    ├── conftest.py
    ├── test_factories.py         # determinism + Pydantic şema
    ├── test_emitters.py          # mock'lu emitter testleri
    └── test_target_matrix.py     # izin matrisi
```

## Faz Yol Haritası

Her faz **bağımsız test edilebilir** ve **geri alınabilir** bir teslim eder. Bir önceki faz tamamlanıp doğrulanmadan sonraki faza geçilmez.

| Faz | Başlık | Çıktı | Risk |
|---|---|---|---|
| **Faz 0** | Discovery & Sözleşme Tespiti | Endpoint envanteri + RabbitMQ routing matrisi | Düşük |
| **Faz 1** | Servis İskeleti & Config | `DataGenService/` boş ama ayağa kalkan FastAPI + healthz | Düşük |
| **Faz 2** | Factory Katmanı | Pydantic-DTO factory'ler, deterministik seed | Düşük |
| **Faz 3** | `file_emitter` + `timeseries_history` | ML parquet çıktısı (DB'ye dokunmaz) | Düşük |
| **Faz 4** | `rest_emitter` + `seed_baseline` | Backend'e seed verisi basma | Orta |
| **Faz 5** | `rabbit_emitter` + `task_load` | LMS event hattı stres | Orta-Yüksek |
| **Faz 6** | `agv_traffic` | Backend yerleştirme/toplama yoğun trafik | Yüksek |
| **Faz 7** | API + CLI Konsolidasyonu | `/scenarios/{name}/run` + Typer + JSON özet | Düşük |
| **Faz 8** | Compose Entegrasyonu & Docs | `data-gen` servisi + CLAUDE.md + runbook + commit | Düşük |

---

### Faz 0 — Discovery & Sözleşme Tespiti ✅

**Hedef:** Faz 4-6'da kullanılacak Backend endpoint kontratlarını ve RabbitMQ topolojisini netleştir.

- [x] `BackendProje/app/api/v1/routers/` taraması: ürün, raf, palet, lot, sipariş, yerleştirme görev, toplama görev yazma uçları listesi (~25 endpoint, 5 grup).
- [x] Her uç için: HTTP method, path, DTO referansı, `Idempotency-Key` desteği, auth gerekliliği tablo halinde çıkarıldı.
- [x] RabbitMQ topolojisi doğrulandı: exchange `depo.events`, routing key `lms.gorev_performans.<event_tipi>`, queue `depo.lms.operator_metrikleri`, DLX `depo.events.dlx`, DLQ `depo.lms.operator_metrikleri.dlq`.
- [x] `PerformansEventTipi` (`GOREV_BASLATILDI`, `GOREV_TAMAMLANDI`, `GOREV_IPTAL`) ve `PerformansGorevTipi` (`yerlestirme`, `toplama`) enum değerleri çıkarıldı.
- [x] AGV → yerleştirme akış bağlantısı doğrulandı (AgvSim'e doğrudan dokunmama kuralı kaynak kodla teyit edildi).
- [x] **Çıktı:** `DataGenService/docs/endpoint_envanteri.md` yazıldı.

**Doğrulama:** Liste eksiksiz, her senaryo için en az bir hedef uç belirlendi.

#### 🚨 Faz 0 Kritik Bulgular (Faz 1 öncesi cevaplanmalı)

1. **Auth sözleşmesi çatışması:** CRUD endpoint'lerinin tamamı **JWT Bearer** (`get_current_user` / `require_role`) bekliyor; `X-Internal-Api-Key` yalnız servisler arası callback uçlarında kabul ediliyor (`agv_callbacks`, `belge_taslaklari`, `excel_ai`). DataGenService'in REST emitter'ı CRUD uçlarına veri basacağı için iki seçenek var:
   - **(A) JWT yolu (MVP önerisi):** Login akışı + token cache + refresh; admin user ile.
   - **(B) Backend'de `/api/internal/*` seed router'ları:** `internal_api_key_verify` dependency'li. Kapsam genişlemesi.
2. **`task_load --target=rabbit` semantiği:** Consumer mesajdaki `event_id` ile DB'den outbox satırını okur. Saf event yayını DB'de karşılık bulamazsa DLQ'ya düşer. Bu mod **anlamlı LMS yükü** değil, yalnız **yük testi** sağlar. Anlamlı LMS aggregator yükü için `--target=rest` tercih edilmeli (use case → outbox doğal akışı).

> Faz 1 başlamadan önce **(1)** numaralı maddeye karar verilmesi gerekiyor. Detay: `DataGenService/docs/endpoint_envanteri.md` §0.

**🔒 Karar (2026-05-15):** **(A) JWT yolu** seçildi. DataGenService başlangıçta `/api/auth/login` ile admin user üzerinden token alır; `Authorization: Bearer <token>` header'ı ile CRUD uçlarına basar. `X-Internal-Api-Key` yalnız callback uçları (kapsam dışı) için tanımlıdır. Backend tarafında ek router eklenmez.

Config'e eklenen alanlar (Faz 1'de):
- `BACKEND_BASE_URL` — Backend FastAPI tabanı (`http://backend:8000` compose içi / `http://127.0.0.1:8000` host).
- `DATAGEN_ADMIN_USERNAME`, `DATAGEN_ADMIN_PASSWORD` — Login akışı.
- `JWT_REFRESH_BUFFER_SEC` (default 60) — Access token süresi dolmadan ne kadar önce refresh tetiklensin.

---

### Faz 1 — Servis İskeleti & Config ✅

**Hedef:** Port 8005'te ayağa kalkan boş FastAPI servisi.

- [x] `DataGenService/` klasörü, `main.py` (`/healthz` döner), `requirements.txt` + `requirements-test.txt`, `Dockerfile`, `README.md`, `pytest.ini`, `tests/conftest.py`.
- [x] `app/core/config.py` (pydantic-settings): `BACKEND_BASE_URL`, `DATAGEN_ADMIN_USERNAME`, `DATAGEN_ADMIN_PASSWORD`, `JWT_REFRESH_BUFFER_SEC`, `RABBITMQ_URL`, `RABBITMQ_EXCHANGE=depo.events`, `DEFAULT_SEED=42`, `LOCALE=tr_TR`, `OUTPUT_DIR=../ml_models/talep_tahmin/data/raw`, `BATCH_SIZE=500`, `CONCURRENCY=10`, `HTTP_TIMEOUT_SEC=30`, `HTTP_MAX_RETRIES=3`. Faz 0 kararı gereği `INTERNAL_API_KEY` kaldırıldı (kapsam dışı).
- [x] `cli.py` Typer iskeleti — `info` (ayarları yazdırır) + `run <scenario>` (placeholder, Faz 7'de aktif).
- [x] `app/api/routers/healthz.py` — `GET /healthz` → `{"status":"ok","service":"data-gen"}`.
- [x] `tests/test_health.py` — `test_healthz_returns_ok` + `test_settings_defaults_are_sane`.

**Doğrulama (Yapıldı):**
- ✅ `TestClient` üzerinden `/healthz` → `200 {"status":"ok","service":"data-gen"}`.
- ✅ `pytest -m unit` → **2 passed**.
- ✅ `ruff check .` → **All checks passed**.
- ✅ Config defaults: `batch_size=500`, `concurrency=10`, `locale=tr_TR`, `rabbitmq_exchange=depo.events`.

**Notlar:**
- `DataGenService/__init__.py`, `app/__init__.py`, `app/core/__init__.py`, `app/api/__init__.py`, `app/api/routers/__init__.py`, `tests/__init__.py` boş paket dosyaları eklendi.
- `tests/conftest.py` her testte `DATA_GEN_ENV_FILE=/dev/null` ayarı ile `.env` etkisini izole eder ve `get_settings.cache_clear()` çağırır.
- `requirements.txt`: FastAPI 0.115, pydantic 2.9, typer 0.12, httpx 0.27, aio-pika 9.4, faker 30.1, mimesis 18.0, factory-boy 3.3, pandas 2.2, pyarrow 17.0. `requirements-test.txt` ek olarak pytest + pytest-asyncio + respx.

---

### Faz 2 — Factory Katmanı

**Hedef:** Pydantic DTO döndüren, deterministik (seed'li), ilişkisel bütünlüklü factory havuzu.

- [ ] `app/factories/base.py` — `BaseFactory` (Faker locale `tr_TR`, seed parametresi).
- [ ] Referans havuz factory'leri: `UrunFactory`, `RafFactory`.
- [ ] Bağımlı factory'ler: `PaletFactory`, `LotFactory`, `SiparisFactory`, `YerlestirmeGorevFactory`, `ToplamaGorevFactory`, `TalepZamanSerisiFactory`.
- [ ] `tests/test_factories.py`: aynı seed → aynı çıktı; Pydantic validasyon; referans bütünlüğü (palet → ürün; lot → palet).

**Doğrulama:** `pytest -m unit tests/test_factories.py` yeşil; iki ayrı `seed=42` koşusu byte-by-byte aynı.

---

### Faz 3 — `file_emitter` + `timeseries_history`

**Hedef:** ML eğitim verisi varsayılan akışı (DB'ye dokunmaz, en düşük risk).

- [ ] `app/infrastructure/emitters/base.py` — `IEmitter` Protocol (`emit_batch`, `summary`).
- [ ] `app/infrastructure/emitters/file_emitter.py` — `pyarrow` ile CSV + Parquet; `OUTPUT_DIR` altına yazar.
- [ ] `app/scenarios/timeseries_history.py` — `TalepZamanSerisiFactory` ile T gün × P ürün satış geçmişi üretir, parquet'e yazar.
- [ ] `tests/test_emitters.py::test_file_emitter` + `tests/test_scenarios.py::test_timeseries_history_file`.

**Doğrulama:** `python -m datagen run timeseries_history --count 100 --target file` → `ml_models/talep_tahmin/data/raw/talep_gecmis_*.parquet` üretildi; `pyarrow` ile okunabilir; şema (`tarih`, `urun_kodu`, `miktar`, ...) doğru.

---

### Faz 4 — `rest_emitter` + `seed_baseline`

**Hedef:** Backend'e idempotent, throttle'lı seed verisi basma.

- [ ] `app/infrastructure/emitters/rest_emitter.py` — HTTPX `AsyncClient`, `Semaphore(CONCURRENCY)`, `BATCH_SIZE` paketleri, `X-Internal-Api-Key`, `Idempotency-Key`, exponential backoff (`0.5s → 1s → 2s → 4s`, max 3 retry).
- [ ] `app/scenarios/seed_baseline.py` — ürün → raf → palet → lot sırasında REST yayını.
- [ ] `tests/test_emitters.py::test_rest_emitter_mock` (HTTPX mock transport ile retry + idempotency-key davranışı).
- [ ] `tests/test_target_matrix.py` — `seed_baseline` yalnız `rest` kabul eder.

**Doğrulama:** `seed_baseline --count=50 --target=rest` → `docker compose logs backend` 50 başarılı insert; aynı seed ile tekrar koş → backend Idempotency-Key sayesinde duplicate üretmez; DB'de sayım eşleşir.

---

### Faz 5 — `rabbit_emitter` + `task_load`

**Hedef:** LMS event hattını sentetik yükle stres et.

- [ ] `app/infrastructure/emitters/rabbit_emitter.py` — `aio-pika` confirm + persistent + mandatory; routing key `lms.gorev_performans.<event_tipi>`; `depo.events` exchange.
- [ ] `app/scenarios/task_load.py` — `target=rest` (use case → outbox doğal akışı) **veya** `target=rabbit` (doğrudan event yayını).
- [ ] `tests/test_emitters.py::test_rabbit_emitter` (aio-pika fake/in-memory).

**Doğrulama:** `task_load --target=rabbit --count=200` → RabbitMQ Management UI'da `depo.lms.operator_metrikleri` queue 200 mesaj; consumer ardından işler; DLQ boş. `task_load --target=rest --count=50` → Backend log'unda görev oluşturma çağrıları; `gorev_performans_eventleri` tablosunda outbox satırları artar.

---

### Faz 6 — `agv_traffic`

**Hedef:** Backend yerleştirme/toplama uçlarına yoğun trafik; AgvSimService'e doğrudan dokunmaz.

- [ ] `app/scenarios/agv_traffic.py` — yalnız `target=rest`; mevcut `rest_emitter` üzerinden.
- [ ] Target izin matrisinde `agv_traffic` × {`rabbit`, `file`} → `422`.
- [ ] `tests/test_target_matrix.py::test_agv_only_rest`.

**Doğrulama:** `agv_traffic --target=rest --count=500` → Backend görev sayısı 500 artar; `docker compose logs agv-sim` Backend tarafından tetiklenen aktiviteyi gösterir (DataGen → AgvSim direkt çağrı **yok**, network trace'te `:8002` görünmez).

---

### Faz 7 — API + CLI Konsolidasyonu

**Hedef:** Tüm senaryoları tek arayüzden çağırılabilir hale getir.

- [ ] `main.py`'a `POST /scenarios/{name}/run` body `{count, seed, target, batch_size, concurrency}`.
- [ ] İzinsiz target → `422 Unprocessable Entity` (matrise göre).
- [ ] Typer: `python -m datagen run <scenario> --count … --seed … --target … --batch-size … --concurrency …`.
- [ ] Çalışma sonunda JSON özet (toplam, başarı, hata, süre, p95 latency).
- [ ] `tests/test_api.py` + `tests/test_cli.py`.

**Doğrulama:** Her 4 senaryo hem API hem CLI üzerinden çalışır; izinsiz target reddedilir; özet JSON şemasına uygun.

---

### Faz 8 — Compose Entegrasyonu & Docs

**Hedef:** Servisin dev stack'e dahil edilmesi ve dokümantasyon.

- [ ] `compose.yml`'a `data-gen` servisi (port 8005, `depends_on: [backend, rabbitmq]`, `INTERNAL_API_KEY` paylaşımı).
- [ ] `infra/env/dev.env`'e `DATA_GEN_*` değişkenleri.
- [ ] `CLAUDE.md`: Main Directories, Common Commands, Important Notes (port 8005) güncelle.
- [ ] `docs/agent/data-gen-service.md` runbook: senaryo katalogu, target matrisi, hacim/throttle ayarları, AGV-Backend-only kuralı, ML dosya çıktı şeması, sorun giderme.
- [ ] Dar bir commit; PR'de "Test plan" Faz başına smoke listesi.

**Doğrulama:** `docker compose up -d data-gen` ayakta; `curl -H "X-Internal-Api-Key: …" :8005/healthz` 200; `CLAUDE.md` ve `docs/agent/data-gen-service.md` güncel; commit dar, alakasız refactor yok.

## Doğrulama Özeti

| Kontrol | Komut / Yol | Beklenen |
|---|---|---|
| Servis sağlığı | `curl :8005/healthz` | `{"status":"ok"}` |
| Unit testler | `pytest -m unit` | Yeşil |
| Lint | `ruff check .` | Hatasız |
| REST yayını | `seed_baseline --count=50 --target=rest` | Backend log'unda 50 başarılı insert, Idempotency-Key tekrarında 200/idempotent |
| RabbitMQ yayını | `task_load --target=rabbit --count=200` | `depo.lms.operator_metrikleri` queue 200, DLQ 0 |
| Dosya çıktısı | `timeseries_history --target=file` | `ml_models/talep_tahmin/data/raw/talep_gecmis_*.parquet` üretildi, şema doğrulandı |
| AGV trafiği | `agv_traffic --target=rest --count=500` | Backend yerleştirme/toplama görev sayısı artar, AgvSimService'e direkt çağrı **yok** |

## Açık Konu

Yok — hacim, çift modlu varsayılan ve AGV bağlantı yönü kararlaştırıldı.
