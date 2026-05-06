# CLAUDE.md

This file is the operational reference for AI coding agents working in this repository.

## Project Overview

**Depo Yönetim Sistemi (WMS)** — Full-stack warehouse management system with lot/pallet tracking, putaway/pick task workflows, production pallet intake, and mobile terminal PWA. FastAPI backend (Clean Architecture) + React (Vite) frontend + AI doğal dil sorgu servisi (LangChain + Ollama).

---

## Build, Lint, Typecheck ve Test Komutları

### Backend (FastAPI — `BackendProje/`)

```bash
# Dependency kurulumu
cd BackendProje
pip install -r requirements.txt
pip install -r requirements-test.txt   # test bağımlılıkları (pytest, httpx, factory-boy, pytest-cov)

# Development server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Lint (ruff)
ruff check .

# Type check (pyright — basic mode, sadece app/ dizini)
pyright

# Tüm testleri çalıştır (test DB gerekir: depo_db_test)
pytest

# Sadece unit testler
pytest -m unit

# Sadece integration testler
pytest -m integration

# Sadece API testler
pytest -m api

# Sadece concurrency testler
pytest -m concurrency

# Tek test dosyası
pytest tests/unit/test_feature_flags.py

# Tek test case (isim pattern'i ile)
pytest -k "test_token_rotation"

# Coverage raporu
pytest --cov=app --cov-report=term --disable-warnings -q --tb=short

# Seed data (admin + depocu kullanıcı)
python seed.py

# Alembic migration
alembic upgrade head
alembic revision --autogenerate -m "migration_aciklamasi"
```

### Frontend (React + Vite — `ReactProje/`)

```bash
cd ReactProje

# Dependency kurulumu
npm install

# Development server (https://localhost:5173, HTTPS + mkcert)
npm run dev

# Lint (ESLint 9 flat config)
npm run lint

# Production build
npm run build

# Preview (production build serve)
npm run preview
```

### WmsAiService (LangChain + Ollama — `WmsAiService/`)

```bash
cd WmsAiService

# Dependency kurulumu
pip install -r requirements.txt

# Development server (port 8001 önerilir, backend 8000'de çalışır)
uvicorn main:app --reload --host 127.0.0.1 --port 8001

# Ollama model (varsayılan: qwen2.5-coder:7b)
ollama pull qwen2.5-coder:7b

# DB view'larını oluştur (ilk kurulumda bir kez)
mysql -u root -p depo_yonetim < views.sql
```

> **Not:** Frontend'te TypeScript kullanılmıyor; tüm dosyalar `.js` / `.jsx`.

---

## Tech Stack

### Backend
- **Language/Runtime:** Python 3.x
- **Framework:** FastAPI
- **ORM:** SQLAlchemy (declarative)
- **Database:** MySQL (PyMySQL driver, charset=utf8mb4)
- **Migration:** Alembic + standalone `migrate_*.py` scriptleri
- **Auth:** JWT (python-jose) + bcrypt (passlib), refresh token desteği
- **Settings:** pydantic-settings (`.env` tabanlı)
- **Rate limiting:** slowapi
- **Scheduler:** APScheduler (rapor zamanlama, staging uyarı)
- **Email:** fastapi-mail (SMTP)
- **Lint:** ruff
- **Type check:** pyright (basic mode)
- **Test:** pytest, httpx (TestClient), factory-boy, pytest-cov

### Frontend
- **Framework:** React 19 + Vite 7
- **Routing:** react-router-dom v7
- **Styling:** Tailwind CSS v4 (@tailwindcss/vite plugin)
- **State/Data fetching:** TanStack React Query v5
- **Animation:** Framer Motion
- **Charts:** Recharts
- **Icons:** lucide-react
- **Toast:** react-hot-toast
- **Barcode/QR:** @zxing/library, html5-qrcode, qrcode.react, jsbarcode
- **Export:** xlsx (Excel), jspdf + jspdf-autotable (PDF)
- **HTTP:** Axios
- **PWA:** vite-plugin-pwa + workbox
- **HTTPS (dev):** vite-plugin-mkcert
- **Lint:** ESLint 9 (flat config) + react-hooks + react-refresh
- **Bundle analysis:** rollup-plugin-visualizer

### WmsAiService (AI Sorgu Servisi)
- **Language/Runtime:** Python 3.x
- **Framework:** FastAPI
- **LLM orchestration:** LangChain (LCEL) + langchain-ollama (ChatOllama)
- **Local LLM:** Ollama (varsayılan model: `qwen2.5-coder:7b`)
- **Database:** MySQL (PyMySQL driver, charset=utf8mb4) — read-only `depo_ai_reader` kullanıcısı
- **SQL execution:** SQLAlchemy + LangChain `SQLDatabase` (view_support=True)
- **Settings:** python-dotenv (`.env` tabanlı)

---

## Project Structure

```
BackendProje/
├── main.py                    # FastAPI app entry point, router kayıtları, CORS, lifespan
├── database.py                # SQLAlchemy engine + SessionLocal
├── models.py                  # Tüm SQLAlchemy ORM modelleri (tek dosya)
├── schemas.py                 # Legacy Pydantic modelleri (runtime büyük ölçüde DTO'lara taşındı; bazı testlerde kullanılır)
├── limiter.py                 # slowapi rate limiter instance
├── seed.py                    # İlk veri yükleme (admin, depocu)
├── alembic/                   # Alembic migration yapılandırması
│   └── versions/              # Migration dosyaları
├── app/                       # Clean Architecture katmanları
│   ├── core/                  # Domain katmanı
│   │   ├── config.py          # Settings (pydantic-settings) + FeatureFlags
│   │   ├── auth.py            # JWT + bcrypt helpers, get_current_user, require_role
│   │   ├── constants.py       # Sabitler
│   │   ├── barcode.py         # Barkod üretim yardımcıları
│   │   ├── idempotency.py     # İdempotency key desteği
│   │   ├── entities/          # Domain entity dataclass'ları
│   │   ├── repositories/      # Abstract repository interface'leri
│   │   ├── services/          # Domain service'ler (FEFO, kapasite, yerleştirme alg., palet giriş/çıkış)
│   │   └── exceptions/        # Domain exception sınıfları
│   ├── application/           # Uygulama katmanı
│   │   ├── use_cases/         # Use case sınıfları
│   │   ├── dto/               # Data Transfer Object'ler
│   │   └── helpers.py         # Yardımcı fonksiyonlar
│   ├── infrastructure/        # Altyapı katmanı
│   │   ├── persistence/       # SQLAlchemy repository implementasyonları + mappers
│   │   ├── di/                # Dependency Injection container + domain modülleri
│   │   │   ├── container.py   # Ana re-export hub
│   │   │   └── modules/       # Domain-odaklı DI modülleri
│   │   ├── config/            # ERP config
│   │   ├── services/          # Infra service implementasyonları (ERP, mock, SQL seri no)
│   │   └── scheduler/         # APScheduler jobs (rapor, staging uyarı)
│   └── api/                   # API katmanı
│       └── v1/routers/        # FastAPI router dosyaları
├── core/                      # Birleşik exception handler'lar (APIException + generic)
├── tests/                     # Test altyapısı
│   ├── conftest.py            # Merkezi fixture'lar (engine, db_session, client, auth)
│   ├── factories/             # factory-boy factory'leri
│   ├── unit/                  # Unit testler (+ iç içe dto/, entities/, routers/, services/, use_cases/)
│   ├── integration/           # Integration testler (concurrency, idempotency, putaway E2E)
│   └── api/routers/           # API endpoint testleri
├── migrate_*.py               # Standalone migration scriptleri (elle çalıştırılır)
├── uploads/                   # Kullanıcı yükleme dizini
├── .env.example               # Ortam değişkeni şablonu
├── .env.test                  # Test ortam değişkenleri
├── pyproject.toml             # Pyright yapılandırması
├── pytest.ini                 # Pytest marker ve filtreleri
└── .coveragerc                # Coverage ayarları

ReactProje/
├── src/
│   ├── main.jsx               # React entrypoint, PWA registration
│   ├── App.jsx                # Route tanımları, PrivateRoute/RoleRoute guards
│   ├── index.css              # Global Tailwind styles + custom CSS
│   ├── contexts/              # AuthContext, AuthProvider, ThemeContext
│   ├── providers/             # QueryProvider (TanStack React Query)
│   ├── lib/                   # queryClient singleton
│   ├── queries/               # TanStack Query hooks + queryKeys (domain-based)
│   ├── services/              # Axios API instance + endpoint fonksiyonları
│   ├── hooks/                 # Custom hooks (useAsync, useBarcodeScanner, useTerminalScanInput)
│   ├── components/
│   │   ├── layout/            # DashboardLayout, DepocuLayout, TerminalLayout, Header, Sidebar
│   │   ├── common/            # Ortak UI bileşenleri
│   │   ├── depocu/            # Depocu'ya özel bileşenler
│   │   ├── palet/             # Palet bileşenleri
│   │   ├── PrivateRoute.jsx   # Auth guard
│   │   └── RoleRoute.jsx      # Role-based guard
│   ├── pages/                 # Sayfa bileşenleri + alt dizinler
│   │   ├── terminal/          # Mobil terminal sayfaları (GorevListesi, Yerlestirme, UretimKabul)
│   │   └── depocu/            # Depocu ana sayfası, kabul seçim
│   ├── utils/                 # Yardımcılar (barcode, exportUtils, hata)
│   └── pwa/                   # PWA registration
├── public/                    # Statik dosyalar, PWA ikonları
├── vite.config.js             # Vite yapılandırması (proxy, PWA, chunks, security headers)
├── eslint.config.js           # ESLint 9 flat config
└── package.json               # npm bağımlılıkları

WmsAiService/
├── main.py                    # FastAPI app entry point, endpoint tanımları (/api/ai/*)
├── chains.py                  # LangChain LCEL pipeline (SQL üret → çalıştır → self-correct → cevapla)
├── prompts.py                 # Sistem promptları, şema açıklaması, few-shot örnekleri (Türkçe)
├── answerer.py                # Cevap üretim katmanı (template-first; LLM yalnızca verbose modda)
├── list_renderer.py           # Çok-satır LIST sonuçlar için deterministik Türkçe template renderer
├── result_formatter.py        # SQL sonuçlarını yapılandırılmış formata çevirir (intent: SCALAR/EMPTY/LIST)
├── sql_guard.py               # SQL güvenlik katmanı (SELECT-only, whitelist, yasaklı keyword'ler)
├── memory.py                  # In-memory konuşma hafızası (session_id bazlı, LRU + TTL)
├── views.sql                  # 9 adet read-only MySQL view tanımı + depo_ai_reader GRANT'ları
├── requirements.txt           # Python bağımlılıkları
├── .env                       # Ortam değişkenleri (DB bağlantı, Ollama ayarları)
└── venv/                      # Python sanal ortam (generated)
```

---

## Code Style Guidelines

### Backend (Python)
- **Linter:** ruff (`ruff check .`)
- **Type checking:** pyright, basic mode, sadece `app/` dizini
- **Fonksiyon/değişken isimleri:** snake_case, Türkçe (ör. `get_urun_listele_uc`, `stok_miktari`)
- **Sınıf isimleri:** PascalCase, Türkçe (ör. `YerlestirmeGorevi`, `PaletGirisService`)
- **Clean Architecture katman disiplini:** `core` → `application` → `infrastructure` → `api` (iç katman dış katmanı import etmez)
- **Dependency Injection:** `Depends()` tabanlı; factory fonksiyonları `app/infrastructure/di/modules/` altında domain modülleri olarak tanımlanır, `container.py` üzerinden re-export edilir
- **Use case pattern:** Yeni iş akışlarında router → use case → repository zinciri tercih edilir; `auth`, idempotency ve bazı stok/terminal endpoint'lerinde sınırlı doğrudan `Session` kullanımı vardır
- **Repository pattern:** Abstract repository (`app/core/repositories/`) → SQLAlchemy implementasyonu (`app/infrastructure/persistence/repositories/`)
- **Entity pattern:** Domain entity'leri `app/core/entities/` altında dataclass olarak tanımlanır; mapper'lar ORM ↔ entity dönüşümü yapar
- **Error handling:** Domain exception'lar (`app/core/exceptions/`) → `APIException` (HTTP status + code + detail) → merkezi exception handler
- **Auth:** `get_current_user` dependency, `require_role("admin")` factory pattern
- **Loglama:** `SistemLog` kaydı kritik CRUD işlemlerinde router'lardan yazılır

### Frontend (JavaScript/JSX)
- **Linter:** ESLint 9 flat config, `no-unused-vars` (ignore `^[A-Z_]` pattern)
- **Dosya formatı:** `.js` / `.jsx` (TypeScript yok)
- **Component pattern:** Fonksiyonel bileşenler + hooks
- **Data fetching:** TanStack React Query (`queries/` dizininde domain-based hooks, `queryKeys.js` merkezi key yapısı)
- **HTTP client:** Axios (`services/api.js`), auto Bearer token injection, 401 → refresh token denemesi → başarısızsa login redirect
- **State management:** React Context (Auth, Theme) + React Query cache
- **Animation:** Framer Motion
- **Styling:** Tailwind CSS v4 (vite plugin entegrasyonu), custom CSS `index.css` içinde
- **Error handling:** `hataMetni(err, fallback)` utility; API hatalarında `detail` → `message` → JS `message` sırası
- **Toast:** `react-hot-toast`
- **Export:** `exportUtils.js` (Excel: xlsx, PDF: jspdf + jspdf-autotable)
- **Debounce:** `use-debounce` kütüphanesi
- **Route guards:** `PrivateRoute` (auth) + `RoleRoute` (rol kontrolü)

---

## Naming Conventions

| Kapsam | Kural | Örnek |
|--------|-------|-------|
| Python dosyaları | snake_case, Türkçe | `yerlestirme_gorevi_use_cases.py` |
| Python sınıflar | PascalCase | `PaletGirisService`, `UrunListeleUseCase` |
| Python fonksiyonlar | snake_case, Türkçe | `get_urun_listele_uc`, `stok_cikis_yap` |
| Python entity'ler | PascalCase | `YerlestirmeGorevi`, `MalKabulIrsaliye` |
| API endpoint'ler | Çoğunlukla `/api/<resource>/`; outbound bazı endpoint'ler `/api/v1/<resource>/` | `/api/urunler/`, `/api/paletler/`, `/api/v1/toplama-gorevleri/` |
| DI factory'ler | `get_<entity>_<islem>_uc` | `get_palet_bazli_stok_service` |
| Test factory'ler | `<Entity>Factory` | `KullaniciFactory`, `PaletFactory` |
| Test dosyaları | `test_<konu>.py` | `test_feature_flags.py` |
| Test marker'lar | `@pytest.mark.<marker>` | `unit`, `integration`, `api`, `concurrency` |
| JSX sayfa dosyaları | PascalCase + `Page.jsx` | `DashboardPage.jsx`, `LotlarPage.jsx` |
| JSX layout dosyaları | PascalCase + `Layout.jsx` | `DashboardLayout.jsx`, `TerminalLayout.jsx` |
| JSX bileşenler | PascalCase | `PrivateRoute`, `PwaInstallButton` |
| JS hook'lar | `use` prefix, camelCase | `useAsync`, `useBarcodeScanner` |
| JS query key'ler | Türkçe camelCase (entity bazlı) | `queryKeys.urunler.list(params)` |
| JS query hook dosyaları | camelCase + `Queries.js` | `productQueries.js`, `malKabulQueries.js` |
| JS service dosyaları | camelCase + `Api.js` | `toplamaGorevleriApi.js` |
| Ortam değişkenleri | UPPER_SNAKE_CASE | `DB_USER`, `JWT_SECRET_KEY`, `FEATURE_URETIM_PALET_PILOT_DEPO_IDS` |

---

## Architecture and Patterns

### Backend — Clean Architecture (4 Katman)

```
api (routers) → application (use cases + DTOs) → core (entities + repositories + services)
                                                   ↑
                                    infrastructure (persistence + DI + scheduler + services)
```

- **Router'lar** çoğunlukla HTTP concern'leri (request parse, response format, auth guard) yönetir; mevcut legacy/adapter noktalarında sınırlı DB erişimi bulunabilir
- **Use case'ler** iş mantığını orkestre eder; repository + domain service'leri inject alır
- **Domain service'ler** çapraz-entity iş kurallarını barındırır (FEFO seçim, kapasite doğrulama, yerleştirme algoritması, palet giriş/çıkış)
- **Repository'ler** abstract (core) → concrete (infrastructure/persistence) ayrımıyla tanımlanır
- **DI container** `Depends()` tabanlı; `app/infrastructure/di/modules/` altında domain-odaklı modüller, `container.py` tek re-export noktası

### Frontend — SPA (Feature-Based Pages)

- **Routing:** `App.jsx` → `react-router-dom` v7, nested `PrivateRoute` + `RoleRoute`
- **Üç farklı layout:** `DashboardLayout` (admin/lojistik ve ortak korumalı sayfalar), `DepocuLayout` (sadece depocu), `TerminalLayout` (mobil terminal)
- **Data fetching:** TanStack React Query + merkezi `queryKeys.js` + domain-based query hook dosyaları
- **Auth akışı:** `AuthProvider` → login → localStorage'a access/refresh token + user → Axios interceptor ile Bearer ekleme → 401'de refresh token → başarısızsa logout
- **Tema:** `ThemeContext` (light/dark mode desteği)
- **PWA:** Service Worker (workbox), offline cache, manifest.json (standalone mode, portrait)

### Roller ve Erişim Kontrolü
- `admin` — Yönetim, raporlama, depo ve terminal rotalarının çoğuna erişim; `/depocu/*` arayüzü sadece `depocu` rolüne açıktır
- `depocu` — Terminal, stok hareketleri, üretim kabul
- `lojistik` — Depolar, depo kroki, stok hareketleri
- `goruntuleyen` — Salt okunur erişim
- `depo_ai_reader` — MySQL DB kullanıcısı (WmsAiService); sadece `ai_*_view` SELECT izni

---

## Project-Specific Rules and Gotchas

### Ortam Değişkenleri
- Backend: `BackendProje/.env` (şablon: `.env.example`). Zorunlu: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `JWT_SECRET_KEY` (min 32 karakter)
- Test: `BackendProje/.env.test` → DB adı `depo_db_test` olmalı (`test` ifadesi içermezse güvenlik kontrolü hata verir)
- Frontend: `ReactProje/.env.local` (isteğe bağlı)
- Feature flag: `FEATURE_URETIM_PALET_PILOT_DEPO_IDS` (boş=kapalı, `TUMU`=tüm depolar, `1,3,5`=belirli depolar)
- Palet veri kaynağı: `PALET_VERI_KAYNAGI` (`LOCAL`, `MOCK`, `ERP`)
- WmsAiService: `WmsAiService/.env`. Zorunlu: `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `DB_NAME`. Opsiyonel: `OLLAMA_MODEL` (def: `qwen2.5-coder:7b`), `OLLAMA_BASE_URL` (def: `http://localhost:11434`), `OLLAMA_ANSWER_MODEL`, `LLM_TEMPERATURE` (def: `0`), `LLM_NUM_CTX` (def: `4096`), `LLM_TIMEOUT` (def: `120`), `MAX_CORRECTION_ATTEMPTS` (def: `2`), `ANSWER_NUM_PREDICT` (def: `40`)

### Stok Hesaplama
- `Urun.stok_miktari` bir `column_property`; `Palet.koli_adedi` üzerinden aktif `Lot` kayıtlarından hesaplanır. **Ürün tablosunda saklanan stok sütunu yoktur.**

### Palet/Lot Durumu
- `Palet.aktif=False` → sevk edilmiş/çıkarılmış palet
- `Lot.aktif=False` → kapatılmış lot
- Üretim paleti state machine: `OLUSTURULDU → KABUL_BEKLIYOR → KABUL_EDILDI → YERLESTIRME_BEKLIYOR → YERLESTIRILDI`; saha hızlı kabul akışında `OLUSTURULDU → KABUL_EDILDI` geçişi de desteklenir (+ `KARANTINA`, `IPTAL_EDILDI`)

### Generated / Dokunulmaması Gereken Dosyalar
- `ReactProje/dist/` — build çıktısı
- `ReactProje/dev-dist/` — PWA dev build
- `ReactProje/stats.html` — bundle analiz raporu (`npm run build` ile oluşur)
- `BackendProje/__pycache__/`, `BackendProje/.venv/`
- `BackendProje/.coverage` — test coverage veritabanı
- `BackendProje/alembic/versions/` — otomatik üretilen migration dosyaları (sadece alembic ile oluştur)
- `WmsAiService/__pycache__/`, `WmsAiService/venv/`

### Migration Kuralları
- **Alembic** resmi migration aracıdır ama projede standalone `migrate_*.py` scriptleri de bulunur (elle çalıştırılır, tekrar çalıştırmaya dayanıklı değil)
- Yeni migration: `alembic revision --autogenerate -m "aciklama"` → `alembic upgrade head`
- `models.py` değiştirildiğinde migration gerekir

### Vite Dev Server
- HTTPS zorunlu (mkcert plugin'i); dev URL: `https://localhost:5173`
- `/api` prefix'li istekler `http://127.0.0.1:8000`'a proxy edilir
- `server.host: true` — LAN erişimi açık
- Build chunk'ları elle bölünmüş: `react-vendor`, `chart-vendor`, `excel-vendor`, `pdf-vendor`, `barcode-vendor`, `ui-vendor`

### Idempotency
- Kritik yazma endpoint'leri `Idempotency-Key` header'ı destekler; tekrarlayan istekler aynı sonucu döner

### Test Altyapısı
- Test DB her `db_session` fixture'ında truncate edilir (izolasyon)
- `factory-boy` factory'leri `tests/factories/` altında; `conftest.py`'daki `admin_user`, `depocu_user`, `lojistik_user` fixture'ları otomatik token üretir
- Test marker'ları: `unit`, `integration`, `api`, `concurrency`
- `.coveragerc` şu dosyaları hariç tutar: `_crud_legacy.py`, `migrate_*.py`, `seed.py`

---

### WmsAiService — Mimari ve Kurallar

#### Pipeline Akışı
```
Kullanıcı sorusu (Türkçe doğal dil)
  → LangChain LCEL: ChatOllama ile SQL üret (few-shot + şema-aware)
  → sql_guard: temizle + SELECT-only + whitelist doğrula
  → SQLAlchemy execute → StructuredResult (intent: SCALAR / EMPTY / LIST)
      → Hata? → self-correction loop (max N deneme, LLM'e hatayı geri ver)
  → Answerer dispatch:
      EMPTY  → sabit Türkçe cümle
      SCALAR → deterministik şablon (LLM yok)
      LIST   → deterministik template (list_renderer); verbose=True ise LLM dener + validation gate
```

#### Güvenlik Katmanı (`sql_guard.py`)
- SELECT-only: INSERT/UPDATE/DELETE/DROP/ALTER ve diğer yasaklı keyword'ler reddedilir
- Whitelist: Yalnızca `ALLOWED_TABLES` setindeki 9 `ai_*_view`'a erişim izni
- SQL yorum satırları (injection vektörü) engellenir
- Birden fazla SQL statement çalıştırılamaz

#### Yeni View Ekleme Kuralları
Yeni bir view eklendiğinde **üç dosya birlikte güncellenmelidir:**
1. `views.sql` — view CREATE + GRANT
2. `sql_guard.py` → `ALLOWED_TABLES` set'ine ekleme
3. `prompts.py` → `SCHEMA_DESCRIPTION` + `FEW_SHOT_EXAMPLES` güncelleme

#### Konuşma Hafızası
- In-memory, thread-safe LRU + TTL (30 dk, max 200 session)
- Session bazlı; `session_id` ile takip soruları desteklenir
- Üretim ortamında Redis ile değiştirilmesi tavsiye edilir

#### Cevap Üretim Stratejisi
- **Template-first:** Çoğu cevap LLM çağrısı olmadan deterministik şablonlarla üretilir
- LLM yalnızca `verbose=True` + LIST intent + validation gate başarılıysa kullanılır
- Bu tasarım küçük/yerel LLM'lerin Türkçe morfoloji bozukluklarını minimize eder

---

## AI Agent Development Checklist

- [ ] Değişiklik yapmadan önce ilgili dosyaları (entity, use case, router, test) oku
- [ ] Clean Architecture katman sınırlarını koru: router → use case → repository; kısa yol açma
- [ ] DI modül desenini takip et: yeni use case/repo → ilgili `di/modules/` dosyasına factory ekle → `container.py`'dan re-export et
- [ ] Backend değişikliği sonrası: `ruff check .` ve `pytest -m unit` çalıştır
- [ ] Frontend değişikliği sonrası: `npm run lint` çalıştır
- [ ] Tüm isimlendirmede Türkçe konvansiyonu koru (model, endpoint, değişken)
- [ ] ORM model değişikliğinde Alembic migration oluştur
- [ ] Yeni API endpoint'i eklerken ilgili use case + router + DI factory + test factory zincirini tamamla
- [ ] Mevcut query key pattern'ine uy (`queryKeys.js`)
- [ ] Davranış değişikliğinde mevcut testleri güncelle; yeni davranış için test yaz
- [ ] Alakasız refactor yapma; değişiklikleri dar ve kapsamlı tut
- [ ] WmsAiService'te yeni view eklerken: `views.sql` + `sql_guard.py` (ALLOWED_TABLES) + `prompts.py` (SCHEMA_DESCRIPTION + FEW_SHOT_EXAMPLES) üçlüsünü birlikte güncelle
