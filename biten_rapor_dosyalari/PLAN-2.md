# Faz 4: Legacy Konsolidasyonu & Test Genişletme

Faz 1-3 ile 17/17 modül + Auth + Dashboard Clean Architecture'a taşındı, eski `crud/`, `services/`, `routers/` silindi. Faz 4'ün amacı: kök seviyedeki legacy dosyaları (`models.py`, `schemas.py`, `auth.py`, `database.py`) Clean Architecture katmanlarına taşımak, `main.py`'deki inline APScheduler mantığını ayırmak ve test coverage'ı %21'den %80+'ya çıkarmak.

## Mevcut Durum (Güncel)

| Kök Dosya | Satır | Tüketici Sayısı | Durum |
|-----------|-------|-----------------|-------|
| `schemas.py` | 722 | **0 dosya** | ⚠️ **Tamamen ölü kod** — hiçbir tüketici kalmadı (auth_dto.py oluşturuldu) |
| `database.py` | 31 | 9 dosya | ⚠️ **Taşınması gerekli** — app/infrastructure/persistence/database.py wrapper haline getirilmeli |
| `models.py` | 523 | 56 dosya | ⚠️ **Taşınması gerekli** — tüm router'lar, repo'lar, mapper, auth, factory'ler bağımlı |
| `auth.py` | 202 | ~25 dosya | ⚠️ **Ayrıştırılması gerekli** — `app.infrastructure.auth/` oluşturulmalı |
| `main.py` (scheduler) | ~50 satır | — | ✅ **Tamamlandı** — `app.infrastructure.scheduler/` zaten oluşturuldu ve aktif |

### Tamamlanan İşlemler (Sonradan)
- ✅ **Adım 5 (APScheduler):** `app/infrastructure/scheduler/` paketi oluşturuldu — `rapor_scheduler.py` ve `__init__.py` mevcut, main.py'den kullanılıyor
- ✅ **Adım 1 (auth_dto.py):** `app/application/dto/auth_dto.py` oluşturuldu — LoginRequestDTO, TokenResponseDTO, KullaniciCreateDTO, RefreshRequestDTO burada
- ✅ **Auth Router Güncellemesi:** `auth.py` router'ı artık `from app.application.dto.auth_dto import ...` kullanıyor

---

## Scope

### In:
- `schemas.py` eliminasyonu (önceki adımlar tamamlandı, **artık silinebilir**)
- `database.py` konsolidasyonu (tek kaynak: `app/infrastructure/persistence/`)
- `models.py` ORM modellerinin `app/infrastructure/persistence/models.py`'ye taşınması
- `auth.py` modülünün `app/infrastructure/auth/` paketine ayrıştırılması
- 15 eksik modülün API testleri + 2 eksik factory + unit test genişletme
- Kök wrapper dosyalarının tamamen silinmesi

### Out:
- Frontend değişiklikleri (API endpoint'leri değişmeyecek)
- `get_current_user()`'ın domain entity döndürmesi (Faz 5+ — şimdilik ORM kalacak)
- Docker/CI ortam değişiklikleri
- Performance/load testing

---

## Action Items

### ~~Adım 1: `schemas.py` Eliminasyonu~~ (Tamamlandı) ✅ `[4a]`

~~1.1 — `app/application/dto/auth_dto.py` oluştur~~ ✅ **Tamamlandı**  
~~1.2 — `app/api/v1/routers/auth.py` güncelle~~ ✅ **Tamamlandı**  
~~1.3 — `tests/unit/entities/test_schemas.py` güncelle~~ ⏳ **Beklemede** (test dosyası hala var, güncellenecek)  
- [ ] **1.4 — `BackendProje/schemas.py` sil** ← Artık güvenli, hiçbir tüketici yok  
- [ ] **1.5 — Doğrula:** `grep -r "from schemas import" BackendProje/` → sıfır sonuç

---

### Adım 2: `database.py` Konsolidasyonu (Düşük Risk) `[4b]`
- [ ] 2.1 — `app/infrastructure/persistence/database.py`'yi genişlet — kök `database.py`'nin tam içeriğini (engine, SessionLocal, Base, get_db) buraya taşı  
- [ ] 2.2 — Kök `BackendProje/database.py`'yi backward-compat wrapper'a dönüştür → `from app.infrastructure.persistence.database import *`  
- [ ] 2.3 — Doğrula: sunucu başlar, testler geçer

---

### Adım 3: ORM Modellerini Infrastructure'a Taşı (Orta Risk) `[4c]`
- [ ] 3.1 — `app/infrastructure/persistence/models.py` oluştur — 21 ORM sınıfını + `stok_miktari` column_property'yi kök `models.py`'den taşı. `Base` import'u `app.infrastructure.persistence.database`'den gelecek  
- [ ] 3.2 — `app/infrastructure/persistence/mappers.py` güncelle — `from models import ...` → `from app.infrastructure.persistence.models import ...`  
- [ ] 3.3 — 18 SA repository dosyasını güncelle — `from models import X as XORM` → `from app.infrastructure.persistence.models import X as XORM`  
- [ ] 3.4 — `main.py` güncelle — `from models import Base, RaporSchedule` → `from app.infrastructure.persistence.models import ...`  
- [ ] 3.5 — `seed.py` güncelle — import yolları  
- [ ] 3.6 — `migrate_*.py` güncelle — import yolları  
- [ ] 3.7 — `tests/conftest.py` güncelle — import yolları  
- [ ] 3.8 — `tests/factories/*.py` güncelle — import yolları  
- [ ] 3.9 — `app/infrastructure/scheduler/rapor_scheduler.py` güncelle — `from models import RaporSchedule` → `from app.infrastructure.persistence.models import RaporSchedule`  
- [ ] 3.10 — Kök `BackendProje/models.py`'yi backward-compat wrapper'a dönüştür (tüm 21 sınıfı re-export)  
- [ ] 3.11 — Doğrula: `python -c "from models import Kullanici"` + sunucu başlar

---

### Adım 4: `auth.py` Clean Architecture'a Taşı (Orta Risk) `[4d]`
- [ ] 4.1 — `app/infrastructure/auth/__init__.py` oluştur (re-export hub)  
- [ ] 4.2 — `app/infrastructure/auth/password_service.py` oluştur — `verify_password`, `get_password_hash`, `hash_token`, `verify_token`  
- [ ] 4.3 — `app/infrastructure/auth/jwt_service.py` oluştur — `create_access_token`, `create_refresh_token`, `verify_and_get_user_from_refresh_token`, JWT sabitleri  
- [ ] 4.4 — `app/infrastructure/auth/dependencies.py` oluştur — `get_current_user`, `require_role`, `oauth2_scheme`  
- [ ] 4.5 — Kök `BackendProje/auth.py`'yi backward-compat wrapper'a dönüştür (tüm export'ları re-export)  
- [ ] 4.6 — 19 router dosyasını güncelle — `from app.core.auth import ...` → `from app.infrastructure.auth import ...` + `from models import Kullanici` → `from app.infrastructure.persistence.models import Kullanici`  
- [ ] 4.7 — `tests/conftest.py` güncelle — auth import yolları  
- [ ] 4.8 — `seed.py` güncelle — auth import yolları  
- [ ] 4.9 — Doğrula: tüm auth endpoint'leri çalışır (login, refresh, me, register, logout)

---

### ~~Adım 5: APScheduler Çıkarma~~ (Tamamlandı) ✅ `[4e]`

~~5.1 — `app/infrastructure/scheduler/__init__.py` oluştur~~ ✅ **Tamamlandı**  
~~5.2 — `app/infrastructure/scheduler/rapor_scheduler.py` oluştur~~ ✅ **Tamamlandı**  
~~5.3 — `main.py`'den scheduler kodu kaldır, `from app.infrastructure.scheduler import RaporScheduler` ile değiştir~~ ✅ **Tamamlandı**  
- [ ] **5.4 — Doğrula:** rapor_scheduler.py içindeki `from models import RaporSchedule` → `from app.infrastructure.persistence.models import RaporSchedule` (Adım 3c sonrası)

### Adım 6: Test Coverage Genişletme `[4f]`

#### 6a — Eksik Factory'ler
- [ ] 6a.1 — `tests/factories/destek_talebi_factory.py` oluştur (`DestekTalebiFactory`)
- [ ] 6a.2 — `tests/factories/sistem_log_factory.py` oluştur (`SistemLogFactory`)
- [ ] 6a.3 — `tests/factories/__init__.py` güncelle — yeni factory'leri `ALL_FACTORIES`'e ekle

#### 6b — API Testleri (15 eksik modül — öncelik sırasıyla)

**Mevcut Durum:** 4 test dosyası var (`test_auth_api.py`, `test_markalar_api.py`, `test_stok_islemleri_api.py`, `test_urunler_api.py`)

**Yüksek Öncelik (temel iş akışı):**
- [ ] 6b.1 — `tests/api/routers/test_kategoriler_api.py` (CRUD + rol kontrolü)
- [ ] 6b.2 — `tests/api/routers/test_depolar_api.py`
- [ ] 6b.3 — `tests/api/routers/test_raflar_api.py`
- [ ] 6b.4 — `tests/api/routers/test_tedarikciler_api.py`
- [ ] 6b.5 — `tests/api/routers/test_lotlar_api.py`
- [ ] 6b.6 — `tests/api/routers/test_paletler_api.py`
- [ ] 6b.7 — `tests/api/routers/test_stok_hareketleri_api.py`

**Orta Öncelik (sipariş akışı):**
- [ ] 6b.8 — `tests/api/routers/test_siparisler_api.py`
- [ ] 6b.9 — `tests/api/routers/test_sevkiyat_planlama_api.py`
- [ ] 6b.10 — `tests/api/routers/test_irsaliyeler_api.py`

**Düşük Öncelik (destek modülleri):**
- [ ] 6b.11 — `tests/api/routers/test_kullanicilar_api.py`
- [ ] 6b.12 — `tests/api/routers/test_destek_api.py`
- [ ] 6b.13 — `tests/api/routers/test_sistem_loglari_api.py`
- [ ] 6b.14 — `tests/api/routers/test_stok_sayim_api.py`
- [ ] 6b.15 — `tests/api/routers/test_raporlar_api.py`
- [ ] 6b.16 — `tests/api/routers/test_dashboard_api.py`

#### 6c — Unit Testler (Use Case mock'larıyla)
- [ ] 6c.1 — `tests/unit/use_cases/test_siparis_use_cases.py`
- [ ] 6c.2 — `tests/unit/use_cases/test_stok_hareketi_use_cases.py`
- [ ] 6c.3 — `tests/unit/use_cases/test_marka_use_cases.py`
- [ ] 6c.4 — Kalan use case'ler için unit testler (modül başına 1 dosya)

---

### Adım 7: Kök Wrapper Dosyalarını Sil (Son Temizlik) `[4g]`
- [ ] 7.1 — Tüm tüketicileri (seed.py, migrate_*.py, test factory'leri, conftest.py) yeni import yollarına güncelle  
- [ ] 7.2 — `BackendProje/schemas.py` sil (Adım 1'de zaten bağımlılık kalmadı)  
- [ ] 7.3 — `BackendProje/models.py` wrapper'ı sil (tüm tüketiciler taşındıktan sonra)  
- [ ] 7.4 — `BackendProje/auth.py` wrapper'ı sil (tüm tüketiciler taşındıktan sonra)  
- [ ] 7.5 — `BackendProje/database.py` wrapper'ı sil (tüm tüketiciler taşındıktan sonra)  
- [ ] 7.6 — Doğrula: `grep -r "from models import\|from app.core.auth import\|from database import\|from schemas import" BackendProje/ --include="*.py"` → yalnızca `app/infrastructure/` altındaki doğru import'lar

---

## Uygulama Sırası ve Risk Tablosu (Güncel)

```
Faz 4a (Tamamlandı ✅):       Adım 1          → schemas.py eliminasyonu         Düşük Risk     [auth_dto.py hazır]
Faz 4b (Altyapı):              Adım 2          → database.py konsolidasyonu      Düşük Risk
Faz 4c (Büyük taşıma):         Adım 3          → ORM modelleri taşıma           Orta Risk      [4b'ye bağımlı]
Faz 4d (Ayrıştırma):           Adım 4          → auth.py ayrıştırma             Orta Risk      [4c'ye bağımlı]
Faz 4e (Tamamlandı ✅):        Adım 5          → APScheduler çıkarma            Düşük-Orta     [zaten çalışıyor]
Faz 4f (Test):                 Adım 6          → Test coverage genişletme       Risk Yok       [4a-4e sonrası ideal]
Faz 4g (Son temizlik):         Adım 7          → Wrapper'ları silme             Orta Risk      [4a-4f tamamlanmış]
```

**Temel prensip:** Her alt-faz backward-compat wrapper pattern kullanır. Kök dosyalar asla ani silinmez — önce wrapper'a dönüşür, tüm tüketiciler taşındıktan sonra silinir. Bu sayede her alt-faz bağımsız deploy edilebilir.

---

## Doğrulama

- [ ] Her alt-faz sonunda: `python -c "from main import app"` → import zinciri kırılmamış
- [ ] `grep -r "from schemas import" BackendProje/` → 0 sonuç (Adım 1.5 sonrası)
- [ ] `grep -r "from models import" BackendProje/ --include="*.py"` → yalnızca wrapper veya infrastructure (Adım 3 sonrası)
- [ ] `grep -r "from auth import" BackendProje/ --include="*.py"` → yalnızca wrapper veya infrastructure (Adım 4 sonrası)
- [ ] CI pipeline: `pytest --cov=. -v` → tüm testler yeşil
- [ ] Sunucu: `uvicorn main:app --reload` → hatasız başlar
- [ ] APScheduler: zamanlı rapor job'u tetiklenir (zaten çalışıyor ✅)

---

## Kritik Dosyalar

| Dosya | Satır | Aksiyon | Mevcut Durum |
|-------|-------|---------|--------------|
| `BackendProje/schemas.py` | 722 | **Sil** (4a) | ⚠️ **Artık silinebilir** — hiçbir tüketici yok |
| `BackendProje/database.py` | 31 | Wrapper → Sil (4b, 4g) | ⏳ **Taşınması gerekli** |
| `BackendProje/models.py` | 523 | Taşı → Wrapper → Sil (4c, 4g) | ⏳ **Taşınması gerekli** |
| `BackendProje/auth.py` | 202 | Ayrıştır → Wrapper → Sil (4d, 4g) | ⏳ **Ayrıştırılması gerekli** |
| `BackendProje/main.py` | ~149 | Scheduler zaten dışarı çıkarıldı | ✅ **Tamamlandı** |
| `app/infrastructure/scheduler/` | — | Zaten oluşturuldu | ✅ **Tamamlandı** |
| `app/application/dto/auth_dto.py` | 75 | Zaten oluşturuldu | ✅ **Tamamlandı** |
| `app/infrastructure/persistence/mappers.py` | 766 | Import yolları güncelle (4c) | ⏳ **Bekliyor** |
| 19 router dosyası | — | Import yolları güncelle (4d) | ⏳ **Bekliyor** |
| 18 SA repository dosyası | — | Import yolları güncelle (4c) | ⏳ **Bekliyor** |

---

## Referans: Faz 4 Sonrası Hedef Dizin Yapısı

```
BackendProje/
├── main.py                          ← ~80 satır (app setup + lifespan + middleware)
├── seed.py                          ← utility script (infrastructure import'ları)
├── app/
│   ├── api/v1/routers/              ← 19 router (infrastructure import'ları)
│   ├── application/
│   │   ├── dto/                     ← 21 DTO (19 modül + auth_dto ✅ + dashboard_dto)
│   │   └── use_cases/               ← 19 use case
│   ├── core/                        ← Domain Layer
│   │   ├── entities/                ← 18 domain entity
│   │   ├── repositories/            ← 18 repo interface
│   │   └── services/                ← domain service'ler
│   └── infrastructure/
│       ├── auth/                    ← YENİ: jwt_service + password_service + dependencies
│       ├── di/container.py
│       ├── persistence/
│       │   ├── database.py          ← TEK KAYNAK (engine, SessionLocal, Base, get_db)
│       │   ├── models.py            ← TEK KAYNAK (21 ORM sınıfı)
│       │   ├── mappers.py
│       │   └── repositories/        ← 18 SA repository
│       ├── scheduler/               ← ✅ ZATEN VAR: rapor_scheduler + RaporScheduler
│       └── services/                ← external service clients
└── tests/
    ├── conftest.py
    ├── factories/                   ← 19 factory (+ 2 YENİ eksik)
    ├── unit/
    │   ├── entities/
    │   └── use_cases/               ← genişletilmiş unit testler
    ├── integration/
    │   └── repositories/
    └── api/routers/                 ← 19 API test dosyası (4 var ✅, 15 eksik)
```

---

## Değişim Özeti (PLAN-2.md v2.0)

### Eklenenler
- ✅ `app/application/dto/auth_dto.py` — LoginRequestDTO, TokenResponseDTO, KullaniciCreateDTO, RefreshRequestDTO
- ✅ `app/infrastructure/scheduler/__init__.py` — RaporScheduler class'ı (wrapper)
- ✅ `app/infrastructure/scheduler/rapor_scheduler.py` — zamanlama_kontrol() ve _zamanlama_email_gonder()
- ✅ `main.py` güncellemesi — `from app.infrastructure.scheduler import RaporScheduler`

### Güncellenenler
- ✅ `app/api/v1/routers/auth.py` — artık `from app.application.dto.auth_dto import ...` kullanıyor
- 📊 **API Test Durumu:** 4 test dosyası mevcut (auth, markalar, stok_islemleri, urunler) — 15 eksik
- 📊 **Factory Durumu:** 17 factory mevcut — 2 eksik (destek_talebi, sistem_log)
- 📊 **scheduler durumu:** Tamamlandı, çalışır durumda

### Artık Geçersiz Olanlar
- ❌ `schemas.py` artık hiçbir tüketici tarafından kullanılmıyor (silinebilir)
- ❌ `auth.py` içindeki Pydantic şemaları artık kullanılmıyor (auth_dto.py'ye taşındı)
- ❌ Eski `main.py` inline APScheduler kodu (artık `app.infrastructure.scheduler`'da)

---

## Open Questions (Güncel)

1. **`seed.py` ve `migrate_*.py` wrapper kullanmaya devam etsin mi?** — Utility script'ler olduğu için wrapper silme fazında (4g) güncellenmeleri yeterli.  
2. **Test coverage threshold (ör. %80) CI'da zorunlu mu olsun?** — İlk aşamada sadece raporlama, ilerleyen fazlarda threshold eklenebilir.  
3. **`get_current_user()` ORM `Kullanici` döndürmeye devam mı etsin?** — Faz 4'te evet (pragmatik). Domain entity dönüşümü Faz 5+'ta değerlendirilebilir.  
4. **APScheduler içindeki `from models import RaporSchedule` ne zaman güncellenecek?** — Adım 3c tamamlandıktan sonra (models.py taşındıktan sonra).
