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

### Faz 2 — Factory Katmanı ✅

**Hedef:** Pydantic DTO döndüren, deterministik (seed'li), ilişkisel bütünlüklü factory havuzu.

- [x] `app/factories/base.py` — `BaseFactory[DTO]` jeneriği (Python 3.12+ `Generic[TypeVar]`), `ReferenceTable` (slots'lu, deterministik `pick(rng)`). Factory başına izole `Faker(locale)` + `random.Random(seed)` instance'ı; `build_many` her çağrıda reseed eder.
- [x] Referans havuz factory'leri: `UrunFactory` (EAN-13 checksum üretimi dahil), `RafFactory` (depo grid'i: `DPO{id}-{koridor}-{kat}-{goz}`).
- [x] Bağımlı factory'ler: `LotFactory` (urun_pool), `PaletFactory` (lot_pool + raf_pool), `SiparisFactory` (urun_pool, kalem tekrarı engelli), `YerlestirmeGorevFactory` (palet_pool + raf_pool), `ToplamaGorevFactory` (sevkiyat_pool, boşsa deterministik fallback), `TalepZamanSerisiFactory` (mevsimsellik + trend + gürültü + ~%5 promosyon).
- [x] `app/factories/schemas.py` — Pydantic v2 DTO'lar (`UrunDTO`, `RafDTO`, `LotDTO`, `PaletDTO`, `SiparisDTO`, `SiparisKalemDTO`, `YerlestirmeGoreviDTO`, `ToplamaGoreviDTO`, `TalepGecmisKaydiDTO`). Ortak `_DataGenBase` config: `str_strip_whitespace=True`, `extra="forbid"`. Backend DTO'larıyla alan uyumlu, bağımsız evrim.
- [x] `tests/test_factories.py` — 18 test, üç eksende kapsam:
  - **Determinism (5):** aynı seed → aynı çıktı, farklı seed → ayrışma, `build_one(k)` == `build_many(>k)[k]`, ardışık `build_many` çağrılarında state reset, negatif count reddi.
  - **Pydantic validasyon (3):** geçerli DTO + kısıt kontrolü, geçersiz override (`fiyat<0`) reddi, bilinmeyen alan reddi (`extra="forbid"`).
  - **Referans bütünlüğü (8):** lot → ürün, palet → lot+raf, sipariş kalemleri unique + havuz içi, yerleştirme görev → palet+raf, toplama görev fallback, talep zaman serisi sayım + determinism + haftanın günü tutarlılığı.
  - **Soyutlama (1):** `BaseFactory` doğrudan instantiate edilemez.

**Doğrulama (Yapıldı):**
- ✅ `pytest -m unit` → **20 passed** (Faz 1 + Faz 2).
- ✅ `ruff check .` → **All checks passed**.
- ✅ MVP ölçek smoke (Python REPL):
  - 1.000 ürün + 300 raf + 2.000 lot + 10.000 palet **deterministik** üretildi.
  - 30 günlük × 1.000 ürün = 30.000 satır talep zaman serisi **0.34 s** içinde üretildi.
- ✅ Aynı seed ile iki ayrı koşum `model_dump()` karşılaştırmasında **byte-by-byte aynı**.

**Notlar (tasarım kararları):**
- `factory-boy` `requirements.txt`'te kaldı (Faz 5+ task_load senaryosunda batch üretimi için kullanılabilir) ama bu fazda dependency-free, type-safe kendi `BaseFactory[DTO]` jeneriğimiz tercih edildi. Global Faker state yok; her factory izole.
- `build_one(k)` reseed + (k-1) atıldıktan sonra k'ıncı kaydı döndürür → çağrı sırasından bağımsız tutarlılık. `build_many` ise tek seferlik sıralı üretim için optimize.
- `TalepZamanSerisiFactory.build_series` generator (lazy) — büyük ürün × gün kombinasyonları parquet emitter'a streamlenebilir (Faz 3).
- `ReferenceTable` `__slots__` ile bellek dostu; FK havuzu olarak `{id: int, **dto_alan}` dict'leri tutar.
- `extra="forbid"` Pydantic config'i ile şema sapması (typo) test ortamında erkenden yakalanır.

---

### Faz 3 — `file_emitter` + `timeseries_history` ✅

**Hedef:** ML eğitim verisi varsayılan akışı (DB'ye dokunmaz, en düşük risk).

- [x] `app/infrastructure/emitters/base.py` — `IEmitter` Protocol + `EmitSummary` dataclass (`total`, `success`, `failed`, `duration_sec`, `p95_latency_ms`, `errors[]`).
- [x] `app/infrastructure/emitters/file_emitter.py` — `FileEmitter` async context manager. **Streaming** `pyarrow.parquet.ParquetWriter` (her batch tek RowGroup), CSV alternatifi. Şema drift'i ikinci batch'te `cast()` ile yakalanır (silent corruption engellenir). `snappy` compression default.
- [x] `app/scenarios/timeseries_history.py` — `TimeseriesHistoryParams` (frozen dataclass, post-init validation: `gun_sayisi≥1`, `urun_count≥1`, `batch_size≥1`, `target='rest'` → `NotImplementedError("Faz 4")`). Akış: `UrunFactory(seed)` → `ReferenceTable` → `TalepZamanSerisiFactory.build_series` generator → `_chunk_iter` (sabit boyut) → `FileEmitter`. Dosya adı `talep_gecmis_{baslangic:%Y%m%d}_seed{seed}_u{urun_count}_g{gun_sayisi}.{ext}` (tekrarlanabilir).
- [x] `ScenarioResult` ortak özet (scenario adı + dosya yolu + metrikler) + `to_dict()` JSON özet için.
- [x] `tests/test_emitters.py` — 6 test: parquet roundtrip, csv roundtrip, boş batch no-op, summary metrikleri, kapalı emitter'a yazım reddi, şema drift yakalama.
- [x] `tests/test_scenarios.py` — 8 test: parquet yazımı, deterministik içerik (iki ayrı run aynı), CSV target, default_output_dir akışı, eksik output_dir reddi, `target='rest'` ⇒ NotImplementedError, geçersiz parametreler, dosya adı kodlaması.

**Doğrulama (Yapıldı):**
- ✅ `pytest -m unit` → **34 passed** (Faz 1 + 2 + 3 toplamı).
- ✅ `ruff check .` → **All checks passed**.
- ✅ MVP ölçek smoke (CLI yerine doğrudan `asyncio.run`):
  - `gun_sayisi=30, urun_count=1000, seed=42` → **30.000 satır parquet** üretildi.
  - **Süre:** 0.38 s. **Dosya:** 67 KB (snappy). **p95 batch latency:** 18.9 ms.
- ✅ `pyarrow.parquet.read_table` ile dosya geri okundu, 30.000 satır + 7 sütun şema doğrulandı.
- ✅ Aynı seed iki ayrı koşumda parquet `to_pylist()` byte-by-byte eşit (`test_timeseries_history_deterministic_file_content`).

**Notlar:**
- `pyarrow 17.0` + `pytest-asyncio 1.3` ortama eklendi (requirements.txt'te zaten tanımlı).
- `FileEmitter` `async __aenter__/__aexit__` destekli; `close()` writer'ı kapatır, idempotent.
- Boş batch yazıldığında parquet writer açılmaz; dosya da oluşturulmaz (gereksiz I/O yok).
- `_chunk_iter` generator boş kuyrukta artık batch yaymaz; bellek O(batch_size) sabit kalır.
- `target='rest'` şu an explicit `NotImplementedError` (Faz 4 placeholder); test bunu doğrular.
- `pytest.ini` mevcut `asyncio_mode = auto` direktifi pytest-asyncio yüklü olduktan sonra aktif oldu; async testler doğal sözdiziminde çalışıyor.

---

### Faz 4 — `rest_emitter` + `seed_baseline` ✅

**Hedef:** Backend'e JWT'li, throttle'lı, retry'lı seed verisi basma.

- [x] `app/infrastructure/auth/jwt_client.py` — `JwtAuthClient`: `/api/auth/login` → cache → `exp` claim decode → buffer sürmeden `/api/auth/refresh` rotation. `asyncio.Lock` ile eşzamanlı caller'larda tek login. Refresh fail olursa login fallback.
- [x] `app/infrastructure/emitters/rest_emitter.py` — `RestEmitter`: endpoint başına instance, paylaşımlı `httpx.AsyncClient` + `asyncio.Semaphore(concurrency)`. Retry politikası: 5xx + network → exponential backoff (`0.5s × 2^n`, ±%20 jitter, max 3), 4xx → tek deneme, 409 + Idempotency-Key → success. Opsiyonel UUID4 `Idempotency-Key` header. `emit_batch_with_responses` extra metodu sıralı response listesi döner.
- [x] `app/scenarios/seed_baseline.py` — `SeedBaselineParams` (frozen, target zorla `'rest'`). Akış: Raf → Ürün → Lot → Palet (FK sırası). Her aşamada response `id` → `ReferenceTable` → bir sonraki factory bunu kullanır. Önemli FK aşaması boş olursa erken `RuntimeError`.
- [x] `app/scenarios/target_matrix.py` — Senaryo × target tek doğruluk kaynağı. `validate_target`, `TargetNotAllowedError`, `ALLOWED_TARGETS`, `DEFAULT_TARGET`. Endpoint envanteri §4 ile eşleşir.
- [x] `tests/test_auth.py` — 6 test (`MockTransport`): cache, refresh trigger, refresh fail → login fallback, login 401, eşzamanlı 10 caller → tek login, eksik credential reddi.
- [x] `tests/test_rest_emitter.py` — 8 test: happy path + ID dönüşü, 5xx retry success, 4xx tek deneme, retry tükenmesi, Idempotency-Key benzersiz UUID, **concurrency limiti gözlemli (max_seen ≤ 3)**, boş batch no-op, 409+idempotency success.
- [x] `tests/test_target_matrix.py` — 7 test: 4 senaryonun izin matrisi tek tek doğrulanır + `SeedBaselineParams(target='file')` reddi + default target izinli küme kontrolü.
- [x] `tests/test_seed_baseline.py` — 3 test: orkestrasyon doğruluğu (4 endpoint × doğru sayı), erken iptal (ürün %100 fail → palet aşaması çağrılmaz, handler assert), kısmi hata akışı (urun_count=6, 2 fail → success=13/15).

**Doğrulama (Yapıldı):**
- ✅ `pytest -m unit` → **58 passed** (Faz 1+2+3+4 toplam).
- ✅ `ruff check .` → **All checks passed**.
- ✅ HTTPX `MockTransport` ile JWT login/refresh, retry, idempotency, concurrency, end-to-end orkestrasyon doğrulandı.
- ⏸️ Canlı backend smoke (`docker compose up backend` + `seed_baseline --count=50 --target=rest`) **Faz 7'de CLI bağlanınca** yapılacak (envanter §0 kararı gereği önce CLI bağlantısı netleşmeli).

**Notlar (tasarım kararları):**
- **JWT yolu (Faz 0 kararı A):** `INTERNAL_API_KEY` config'ten kaldırılmıştı; auth artık `DATAGEN_ADMIN_USERNAME` + `DATAGEN_ADMIN_PASSWORD` üzerinden.
- **Tek emitter / tek endpoint** deseni — `RestEmitter("/api/raflar/")`, `RestEmitter("/api/urunler/")` ayrı instance'lar; ortak `Semaphore` ile global concurrency limiti.
- **ID akışı** — `emit_batch_with_responses` Protocol dışı extra metot (Protocol'ün uniform arayüzünü kirletmemek için). Senaryo response'lardan `id` alanını okuyup `ReferenceTable`'a aktarır; sıralı boş slot'lar (hatalı istekler) atlanır.
- **Idempotency-Key**: Faz 0 envanteri §1.1'e göre `/api/raflar/`, `/api/urunler/`, `/api/lotlar/`, `/api/paletler/` CRUD uçları backend tarafında bu header'ı **desteklemez**. `seed_baseline` re-run senaryosunda duplicate barkod/kod 422'leri beklenir → `failed` sayar, akış devam eder. Header desteği eklenirse (`SeedBaselineParams.idempotency=True`) doğal olarak çalışacak.
- **Backend seed ön koşulu:** `seed_baseline` çalışırken backend'de zaten kategori/marka/tedarikçi/depo/zon mevcut olduğu varsayılır (`BackendProje/seed.py` veya `dev_seed_minimal.sql`). MVP kapsamında DataGen bu beş tabloyu basmaz.
- **Jitter (±%20):** Thundering herd'i azaltır; aynı saniyede yüzlerce istek bir 503 alırsa hep birlikte aynı backoff'a takılmaz.
- **Concurrency limit testi:** `inflight` sayacı handler içinde tutuluyor; gerçek concurrency 3'ü aşmıyor — `Semaphore(3)` doğrulandı.

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
