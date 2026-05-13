# Project Architecture

Detaylı mimari referans. CLAUDE.md, bu dosyaya işaret eder.

## Project Overview

**Depo Yönetim Sistemi (WMS)** — Full-stack warehouse management system: lot/pallet tracking, putaway/pick task workflows, production pallet intake, mobile terminal PWA ve operatör performans (LMS) modülü (transactional outbox + APScheduler aggregator → vardiya KPI'ları + UPH leaderboard). FastAPI backend (Clean Architecture) + React (Vite) frontend + AI doğal dil sorgu servisi (LangChain + Ollama) + AGV/AMR simülasyon servisi (in-memory world + Three.js 3D izleme) + Belge AI mikroservisi (Ollama text + VLM).

## Backend — Clean Architecture (4 Katman)

```
api (routers) → application (use cases + DTOs) → core (entities + repositories + services)
                                                   ↑
                                    infrastructure (persistence + DI + scheduler + services)
```

- **Router'lar** HTTP concern'leri (request parse, response, auth guard); legacy/adapter noktalarında sınırlı doğrudan DB erişimi olabilir.
- **Use case'ler** iş mantığı orkestrasyonu; repository + domain service inject eder.
- **Domain service'ler** çapraz-entity iş kuralları (FEFO seçim, kapasite, yerleştirme algoritması, palet giriş/çıkış).
- **Repository pattern:** Abstract (`app/core/repositories/`) → SQLAlchemy implementasyonu (`app/infrastructure/persistence/repositories/`).
- **Entity pattern:** `app/core/entities/` altında dataclass; mapper'lar ORM ↔ entity dönüşümü yapar.
- **DI container:** `Depends()` tabanlı; `app/infrastructure/di/modules/` altında domain-odaklı modüller, `container.py` tek re-export noktası.
- **Error handling:** Domain exception → `APIException` (status + code + detail) → merkezi handler.
- **Auth:** `get_current_user` dependency, `require_role("admin")` factory.
- **Loglama:** `SistemLog` kritik CRUD'larda router'lardan yazılır.

## Backend Klasör Yapısı (özet)

```
BackendProje/
├── main.py                 # FastAPI entry, router kayıtları, CORS, lifespan
├── database.py             # SQLAlchemy engine + SessionLocal
├── models.py               # Tüm SQLAlchemy ORM modelleri (tek dosya)
├── schemas.py              # Legacy Pydantic modelleri
├── seed.py
├── alembic/versions/       # Migration dosyaları
├── app/
│   ├── core/               # Domain (entities, repositories, services, exceptions, config)
│   ├── application/        # use_cases, dto, helpers
│   ├── infrastructure/     # persistence, di/modules, scheduler, services, config
│   └── api/v1/routers/     # FastAPI router'lar
├── core/                   # Merkezi exception handler'lar
├── tests/                  # conftest + factories + unit/integration/api
├── migrate_*.py            # Standalone migration scriptleri (elle, idempotent değil)
└── pytest.ini, pyproject.toml, .coveragerc
```

## Frontend — SPA (Feature-Based Pages)

- **Routing:** `App.jsx` → `react-router-dom` v7; nested `PrivateRoute` + `RoleRoute`.
- **Üç layout:** `DashboardLayout` (admin/lojistik), `DepocuLayout` (depocu), `TerminalLayout` (mobil terminal).
- **Data fetching:** TanStack React Query + merkezi `queryKeys.js` + domain-based query hook dosyaları.
- **Auth akışı:** `AuthProvider` → login → localStorage'a access/refresh + user → Axios interceptor → 401'de refresh → başarısızsa logout.
- **Tema:** `ThemeContext` (light/dark).
- **PWA:** workbox SW, offline cache, manifest (standalone, portrait).

## Frontend Klasör Yapısı (özet)

```
ReactProje/
└── src/
    ├── main.jsx, App.jsx, index.css
    ├── contexts/                       # AuthContext, ThemeContext
    ├── providers/QueryProvider.jsx
    ├── lib/queryClient.js
    ├── queries/                        # Hooks + queryKeys (domain-based)
    ├── services/                       # Axios api + endpoint dosyaları
    ├── hooks/                          # useAsync, useBarcodeScanner, ...
    ├── components/{layout,common,depocu,palet, PrivateRoute, RoleRoute}
    ├── pages/{...,terminal,depocu}
    ├── utils/                          # barcode, exportUtils, hata
    └── pwa/
```

## Roller ve Erişim Kontrolü

- `admin` — Yönetim, raporlama, depo ve terminal rotalarının çoğu; `/depocu/*` arayüzü sadece `depocu`'ya açıktır.
- `depocu` — Terminal, stok hareketleri, üretim kabul.
- `lojistik` — Depolar, depo kroki, stok hareketleri.
- `goruntuleyen` — Salt okunur.
- `depo_ai_reader` — MySQL DB kullanıcısı (WmsAiService); sadece `ai_*_view` SELECT izni.

## Code Style — Backend (Python)

- Linter: ruff (`ruff check .`).
- Type check: pyright basic, sadece `app/`.
- Fonksiyon/değişken: snake_case Türkçe (`get_urun_listele_uc`, `stok_miktari`).
- Sınıf: PascalCase Türkçe (`YerlestirmeGorevi`, `PaletGirisService`).
- Katman disiplini: `core → application → infrastructure → api` (iç → dış import yasak).

## Code Style — Frontend (JS/JSX)

- ESLint 9 flat config; `no-unused-vars` (`^[A-Z_]` ignore).
- TypeScript yok. `.js` / `.jsx`.
- Fonksiyonel component + hooks; State: Context (Auth, Theme) + React Query.
- HTTP: Axios `services/api.js`; auto Bearer; 401 → refresh.
- Error: `hataMetni(err, fallback)` → `detail` → `message` → JS `message`.
- Toast: `react-hot-toast`. Export: `exportUtils.js` (xlsx, jspdf). Debounce: `use-debounce`.

## Naming Conventions

| Kapsam | Kural | Örnek |
|---|---|---|
| Python dosya | snake_case TR | `yerlestirme_gorevi_use_cases.py` |
| Python sınıf | PascalCase | `PaletGirisService`, `UrunListeleUseCase` |
| Python fonksiyon | snake_case TR | `get_urun_listele_uc` |
| Python entity | PascalCase | `YerlestirmeGorevi`, `MalKabulIrsaliye` |
| API endpoint | `/api/<resource>/`; bazıları `/api/v1/<resource>/` | `/api/urunler/`, `/api/v1/toplama-gorevleri/` |
| DI factory | `get_<entity>_<islem>_uc` | `get_palet_bazli_stok_service` |
| Test factory | `<Entity>Factory` | `KullaniciFactory` |
| Test dosya | `test_<konu>.py` | `test_feature_flags.py` |
| Test marker | `@pytest.mark.<marker>` | `unit`, `integration`, `api`, `concurrency` |
| JSX sayfa | PascalCase + `Page.jsx` | `DashboardPage.jsx` |
| JSX layout | PascalCase + `Layout.jsx` | `TerminalLayout.jsx` |
| JS hook | `use` prefix camelCase | `useBarcodeScanner` |
| Query key | camelCase TR | `queryKeys.urunler.list(params)` |
| Query hook dosya | `<domain>Queries.js` | `productQueries.js` |
| Service dosya | `<domain>Api.js` | `toplamaGorevleriApi.js` |
| Env var | UPPER_SNAKE_CASE | `JWT_SECRET_KEY` |

## Tech Stack

### Backend
Python 3.x · FastAPI · SQLAlchemy (declarative) · MySQL (PyMySQL, utf8mb4) · Alembic + standalone `migrate_*.py` · JWT (python-jose) + bcrypt + refresh token · pydantic-settings · slowapi · APScheduler · fastapi-mail · ruff · pyright basic · pytest + httpx + factory-boy + pytest-cov.

### Frontend
React 19 + Vite 7 · react-router-dom v7 · Tailwind CSS v4 (@tailwindcss/vite) · TanStack React Query v5 · Framer Motion · Recharts · lucide-react · react-hot-toast · @zxing/library + html5-qrcode + qrcode.react + jsbarcode · xlsx + jspdf + jspdf-autotable · Axios · vite-plugin-pwa + workbox · vite-plugin-mkcert · ESLint 9 + react-hooks + react-refresh · rollup-plugin-visualizer.

## Domain Notları

### Stok Hesaplama
- `Urun.stok_miktari` bir `column_property`; `Palet.koli_adedi` üzerinden aktif `Lot` kayıtlarından hesaplanır.
- **Ürün tablosunda saklanan stok sütunu yoktur.**

### Palet/Lot Durumu
- `Palet.aktif=False` → sevk edilmiş/çıkarılmış palet.
- `Lot.aktif=False` → kapatılmış lot.
- Üretim paleti state machine: `OLUSTURULDU → KABUL_BEKLIYOR → KABUL_EDILDI → YERLESTIRME_BEKLIYOR → YERLESTIRILDI`; saha hızlı kabul akışında `OLUSTURULDU → KABUL_EDILDI` direkt; ek durumlar `KARANTINA`, `IPTAL_EDILDI`.

### Idempotency
- Kritik yazma endpoint'leri `Idempotency-Key` header'ı destekler.

### Migration Kuralları
- Alembic resmi araç; standalone `migrate_*.py` scriptleri de var (idempotent değil).
- Yeni migration: `alembic revision --autogenerate -m "aciklama"` → `alembic upgrade head`.
- `models.py` değiştirildiğinde migration gerekir.
- **Migration yazmak yeterli değildir** — her ortamda `alembic upgrade head`; aksi halde `1146 Table doesn't exist`. `main.py` lifespan'inde `_migration_drift_kontrol` log/error verir (prod'da `DEPO_STRICT_MIGRATION=1` ile boot durdurulur).

### Operatör Performans (LMS)
- **Transactional Outbox:** Yerleştirme/toplama use case'leri `IPerformansEventPublisher` ile `gorev_performans_eventleri` tablosuna event yazar (transaction'da atomik). Default: `DbOutboxPerformansEventPublisher`; Faz 5'te RabbitMQ takılabilir.
- **Aggregator:** `MetriklerAggregasyonUseCase` APScheduler ile her 5 dk; outbox → `operator_vardiya_metrikleri` upsert, event'leri `aggregate_edildi=True`. İdempotent.
- **Vardiya = takvim günü (UTC).** UPH = `(yerlestirme + toplama) / (toplam_aktif_saniye / 3600)`, saklanmaz. Hata oranı = `iptal / (tamamlanan + iptal)`.
- **Endpoint:** `/api/operator-performans/{ozet, leaderboard, me, kullanici/{id}}`. Admin/lojistik tüm operatörler; depocu yalnız `/me` ve kendi id'siyle `/kullanici/{id}` (aksi 403). Leaderboard tüm rollere açık.
- **Migration:** `e2f3a4b5c6d7_operator_performans_modulu`.
- **Hook zorunlu:** Yeni yerleştirme/toplama görev geçişi eklenirken publisher çağrısı atlanırsa outbox akışı kırılır.

## Development Checklist

- Değişiklikten önce ilgili dosyaları (entity, use case, router, test) oku.
- Katman sınırlarını koru; router → use case → repository zinciri.
- DI modül deseni: yeni use case/repo → `di/modules/` factory → `container.py` re-export.
- Backend sonrası: `ruff check .` + `pytest -m unit`.
- Frontend sonrası: `npm run lint`.
- Türkçe isimlendirme.
- ORM değişti → Alembic migration + `alembic upgrade head`.
- Yerleştirme/toplama geçişi → LMS publisher hook'unu çağır.
- Yeni endpoint → use case + router + DI factory + test factory zinciri tam.
- Mevcut query key pattern'ine uy.
- Davranış değişiminde testleri güncelle.
- Alakasız refactor yapma; değişiklikleri dar tut.
