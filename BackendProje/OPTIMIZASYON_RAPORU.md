# Depo Yönetim Sistemi — Optimizasyon Analiz Raporu

> **Tarih:** 2026-03-18
> **Kaynak:** GitHub Actions CI test çıktıları + codebase analizi
> **Mevcut Durum:** 67 test PASSED | 57% coverage | 27 warning | 10.67s süre

---

## 1. MEVCUT DURUM ANALİZİ

### 1.1 Test Sonuçları Özeti

| Kategori | Test Sayısı | Durum |
|----------|-------------|-------|
| Unit — Schema Validasyonları | 25 | PASSED |
| Unit — Use Case Testleri | 9 | PASSED |
| Integration — CRUD Testleri | 13 | PASSED |
| API — Router Testleri | 20 | PASSED |
| **TOPLAM** | **67** | **ALL PASSED** |

### 1.2 Coverage Isı Haritası

```
YÜKSEK COVERAGE (>80%)          ORTA COVERAGE (50-80%)         DÜŞÜK COVERAGE (<50%)
─────────────────────────        ──────────────────────         ─────────────────────
models.py           98%          auth.py              70%       crud/siparis        16%
schemas.py          98%          crud/marka           53%       crud/rapor          17%
crud/urun           95%          crud/stok_hareketi   85%       crud/sevkiyat       19%
crud/stok_hareketi  85%          services/marka       70%       crud/irsaliye       19%
routers/auth        84%          services/tedarikci   62%       crud/kategori       20%
app/dto/urun        91%          services/kategori    57%       crud/depo           23%
                                                                crud/destek         23%
                                                                crud/palet          23%
                                                                crud/raf            24%
                                                                crud/lot            28%
                                                                services/stok_sayim 23%
                                                                services/kullanici  31%
                                                                services/rapor      48%
                                                                main.py             54%
                                                                _crud_legacy.py      0%
```

**Genel Coverage: 57%** — Hedef: **80%+**

### 1.3 Warning Analizi (27 Warning)

| Warning Türü | Sayı | Ciddiyet |
|-------------|------|----------|
| PydanticDeprecatedSince20 (`class Config`) | 25 | ORTA — Pydantic V3'te kırılacak |
| SQLAlchemy MovedIn20Warning (`declarative_base()`) | 1 | DÜŞÜK — SA 2.0+ uyumsuzluk |
| passlib `crypt` DeprecationWarning | 1 | YÜKSEK — Python 3.13'te kaldırılacak |

---

## 2. KRİTİK BULGULAR

### 2.1 Hata Riski Yüksek Alanlar (Test Edilmemiş)

1. **`_crud_legacy.py` (1428 satır, %0 coverage)** — Ölü kod mu, aktif mi belirsiz. Coverage'ı sıfır ama `crud/` modülleri tarafından çağrılıyor olabilir. Risk: Referans bozulursa sessiz hata.

2. **Sipariş iş akışı** — `crud/siparis_crud.py` (%16), `app/use_cases/siparis_use_cases.py` (%31). Sipariş oluşturma, güncelleme, kalem yönetimi test edilmemiş. Finansal etki potansiyeli yüksek.

3. **Rapor sistemi** — `crud/rapor_crud.py` (%17), `services/rapor_service.py` (%48). 345 satırlık rapor CRUD'u neredeyse hiç test edilmemiş. Zamanlı rapor tetikleme (`main.py:53-86`) de kapsam dışı.

4. **Stok sayım** — `services/stok_sayim_service.py` (%23, 196 satır). Envanter doğrulama mekanizması test edilmemiş — veri tutarsızlığı riski.

5. **İrsaliye/Sevkiyat** — `crud/irsaliye_crud.py` (%19), `crud/sevkiyat_crud.py` (%19). Lojistik zinciri kırılgan.

### 2.2 Mimari Sorunlar

1. **İkili mimari karmaşası** — Hem eski (`crud/`, `services/`, `routers/`) hem yeni Clean Architecture (`app/`) katmanları paralel çalışıyor. `main.py` her iki yapıyı da import ediyor — bakım yükü çift.

2. **`_crud_legacy.py` hayalet dosya** — 1428 satırlık dosya %0 coverage ile CI'da ölçülüyor. Eğer kullanılmıyorsa coverage'ı düşürüyor, kullanılıyorsa test edilmemiş kritik kod.

3. **`database.py` deprecation** — `declarative_base()` eski import yolu kullanılıyor. SQLAlchemy 2.0 uyumsuzluk riski.

4. **passlib/crypt** — Python 3.13'te `crypt` modülü kaldırılacak. `passlib` alternatifi ya da `bcrypt` doğrudan kullanımı planlanmalı.

### 2.3 Pydantic V2 Migration (25 Warning)

`schemas.py` içinde 25 adet `class Config: from_attributes = True` kullanımı mevcut. Pydantic V3'te bu yapı kaldırılacak.

**Çözüm:** `model_config = ConfigDict(from_attributes=True)` ile değiştirmek.

---

## 3. OPTİMİZASYON PLANI

### Faz 1 — Acil Düzeltmeler (Warning Temizliği)
**Süre:** 1 oturum | **Etki:** 27 warning → 0 | **Risk:** Düşük

| # | Görev | Dosya | Detay |
|---|-------|-------|-------|
| 1.1 | Pydantic `class Config` → `model_config = ConfigDict(...)` | `schemas.py` | 25 warning temizlenir |
| 1.2 | `declarative_base()` → `sqlalchemy.orm.declarative_base()` | `database.py` | 1 warning temizlenir |
| 1.3 | passlib `crypt` → bcrypt direkt kullanım veya passlib güncellemesi | `auth.py` | Python 3.13 uyumluluğu |
| 1.4 | `_crud_legacy.py` durumunu belirle | `_crud_legacy.py` | Kullanılmıyorsa sil veya `--cov-config`'den çıkar |

### Faz 2 — Kritik Test Coverage Artırma
**Süre:** 2-3 oturum | **Etki:** 57% → ~75% | **Öncelik:** Finansal/lojistik riskli alanlar

| # | Modül | Mevcut | Hedef | Test Türü | Detay |
|---|-------|--------|-------|-----------|-------|
| 2.1 | `crud/siparis_crud.py` | 16% | 80% | Integration | Sipariş CRUD + kalem yönetimi |
| 2.2 | `crud/rapor_crud.py` | 17% | 70% | Integration | Şablon/log CRUD, schedule |
| 2.3 | `crud/sevkiyat_crud.py` | 19% | 80% | Integration | Sevkiyat planı oluştur/güncelle |
| 2.4 | `crud/irsaliye_crud.py` | 19% | 80% | Integration | İrsaliye oluştur/güncelle |
| 2.5 | `services/stok_sayim_service.py` | 23% | 75% | Unit + Integration | Sayım başlat/onayla/fark hesapla |
| 2.6 | `services/kullanici_service.py` | 31% | 80% | Unit | Kullanıcı CRUD, rol kontrolü |
| 2.7 | `crud/kategori_crud.py` | 20% | 80% | Integration | Basit CRUD — hızlı kazanım |
| 2.8 | `crud/depo_crud.py` | 23% | 80% | Integration | Basit CRUD — hızlı kazanım |

### Faz 3 — API Endpoint Test Genişletme
**Süre:** 2 oturum | **Etki:** ~75% → ~85% | **Tür:** API (TestClient)

| # | Router | Mevcut | Hedef | Detay |
|---|--------|--------|-------|-------|
| 3.1 | `routers/kategoriler.py` | 75% | 95% | CRUD + yetki testleri |
| 3.2 | `routers/depolar.py` | 75% | 95% | CRUD + yetki testleri |
| 3.3 | `routers/lotlar.py` | 75% | 95% | Lot yaşam döngüsü |
| 3.4 | `routers/paletler.py` | 69% | 95% | Palet aktif/pasif |
| 3.5 | `routers/sevkiyat_planlama.py` | 77% | 95% | Sevkiyat planı endpoint'leri |
| 3.6 | `routers/irsaliyeler.py` | 79% | 95% | İrsaliye endpoint'leri |
| 3.7 | `routers/raporlar.py` | 43% | 80% | Rapor oluşturma/zamanlama |

### Faz 4 — Clean Architecture Geçiş Tamamlama
**Süre:** 3-4 oturum | **Etki:** Bakım maliyeti düşer, test izolasyonu artar

| # | Modül | Durum | Hedef |
|---|-------|-------|-------|
| 4.1 | Kategoriler | Eski mimari | Use case + repository dönüşümü |
| 4.2 | Depolar | Eski mimari | Use case + repository dönüşümü |
| 4.3 | Lotlar | Eski mimari | Use case + repository dönüşümü |
| 4.4 | Paletler | Eski mimari | Use case + repository dönüşümü |
| 4.5 | Kullanıcılar | Eski mimari | Use case + repository dönüşümü |
| 4.6 | `_crud_legacy.py` | Hayalet | Tamamen kaldır |

### Faz 5 — CI/CD Pipeline İyileştirme
**Süre:** 1 oturum | **Etki:** Geliştirici deneyimi

| # | Görev | Detay |
|---|-------|-------|
| 5.1 | Coverage threshold ekle | `--cov-fail-under=75` — PR'lar coverage düşüremez |
| 5.2 | Coverage raporunu artifact olarak kaydet | `--cov-report=html` + actions upload |
| 5.3 | Test parallelization | `pytest-xdist` ile paralel çalıştırma (10.67s → ~5s) |
| 5.4 | Warning'leri hata yap | `filterwarnings = error` (Faz 1 sonrası) |
| 5.5 | Ayrı test stage'leri | Unit (hızlı) → Integration → API sıralaması |
| 5.6 | `_crud_legacy.py` coverage'dan çıkar | `.coveragerc` ile `omit` veya dosyayı sil |

---

## 4. HIZLI KAZANIMLAR (Quick Wins)

Bu değişiklikler minimum eforla maksimum etki sağlar:

### 4.1 Coverage'ı Anında 5-8% Artırma
`_crud_legacy.py` (1428 satır, %0 coverage) coverage hesaplamasından çıkarılırsa:
- Mevcut: 6820 satır, 2934 miss → **57%**
- `_crud_legacy.py` çıkarılırsa: 6122 satır, 2236 miss → **63.5%**

### 4.2 Pydantic ConfigDict Geçişi (25 warning → 0)
```python
# ESKİ (deprecated)
class MarkaResponse(MarkaBase):
    id: int
    class Config:
        from_attributes = True

# YENİ
from pydantic import ConfigDict

class MarkaResponse(MarkaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
```

### 4.3 SQLAlchemy declarative_base Düzeltme (1 warning → 0)
```python
# ESKİ
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# YENİ
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

### 4.4 Basit CRUD Testleri (kategori, depo, tedarikci, raf)
Bu 4 modül basit CRUD pattern'i izliyor — her biri ~5-6 fonksiyon. Tek bir oturumda factory + integration test yazılabilir. Tahmini etki: **+8-10% coverage**.

---

## 5. ÖNCELİK MATRİSİ

```
                        YÜKSEK ETKİ
                            │
         Faz 1 (Warning)   │   Faz 2 (Kritik Coverage)
         Quick Win 4.1      │   Sipariş/Sevkiyat testleri
                            │
   DÜŞÜK EFOR ──────────────┼────────────── YÜKSEK EFOR
                            │
         Faz 5 (CI/CD)     │   Faz 4 (Clean Arch Geçiş)
         Quick Win 4.4      │   Tam mimari dönüşüm
                            │
                        DÜŞÜK ETKİ
```

**Önerilen Sıralama:**
1. Faz 1 + Quick Win 4.1 → Hemen (warnings + sahte coverage düşüşü temizlenir)
2. Quick Win 4.4 → Basit CRUD testleri (kolay coverage artışı)
3. Faz 2 → Kritik iş mantığı testleri
4. Faz 3 → API endpoint testleri
5. Faz 5 → CI/CD pipeline iyileştirmeleri
6. Faz 4 → Clean Architecture geçişi (uzun vadeli)

---

## 6. HEDEF METRİKLER

| Metrik | Şu An | Faz 1 Sonrası | Faz 2 Sonrası | Faz 3 Sonrası |
|--------|--------|---------------|---------------|---------------|
| Test Sayısı | 67 | 67 | ~130 | ~200 |
| Coverage | 57% | 63% | 78% | 85%+ |
| Warnings | 27 | 0 | 0 | 0 |
| CI Süresi | 10.67s | ~10s | ~12s | ~15s (veya xdist ile ~8s) |

---

## 7. RİSK DEĞERLENDİRMESİ

| Risk | Olasılık | Etki | Azaltma |
|------|----------|------|---------|
| Python 3.13 passlib kırılması | Yüksek | Kritik | Faz 1.3'te bcrypt geçişi |
| Pydantic V3 breaking change | Orta | Yüksek | Faz 1.1'de ConfigDict geçişi |
| Sipariş iş akışında sessiz hata | Orta | Kritik | Faz 2.1 sipariş testleri |
| Stok sayım veri tutarsızlığı | Düşük | Kritik | Faz 2.5 sayım testleri |
| CI pipeline yavaşlama | Düşük | Düşük | Faz 5.3 parallelization |

---

## 8. TEST ALTYAPISI ANALİZİ

### 8.1 Mevcut Test Mimarisi

```
tests/
├── conftest.py              ← Ana fixture'lar: engine, db_session, client, auth
├── factories/               ← 10 factory (factory-boy tabanlı)
│   ├── base_factory.py      ← SQLAlchemyModelFactory (commit persistence)
│   ├── kullanici_factory.py ← Cached bcrypt hash (~400ms tasarruf/test)
│   ├── marka_factory.py
│   ├── kategori_factory.py
│   ├── depo_factory.py
│   ├── raf_factory.py       ← SubFactory(DepoFactory)
│   ├── tedarikci_factory.py
│   ├── urun_factory.py      ← SubFactory(Marka + Kategori)
│   ├── lot_factory.py       ← SubFactory(UrunFactory)
│   ├── palet_factory.py     ← SubFactory(Lot + Raf)
│   └── stok_hareketi_factory.py ← SubFactory(Urun + Kullanici)
├── unit/                    ← DB gerektirmez
│   ├── entities/test_schemas.py      (25 test)
│   └── use_cases/test_urun_use_cases.py (9 test, mock-based)
├── integration/             ← Gerçek MySQL DB
│   ├── conftest.py          ← _bind_factories autouse
│   ├── crud/
│   │   ├── test_urun_crud.py         (9 test)
│   │   └── test_stok_hareketi_crud.py (4 test)
│   └── repositories/        ← BOŞ (Clean Arch repo testleri yok!)
└── api/                     ← HTTP TestClient + gerçek DB
    ├── conftest.py          ← _bind_factories autouse
    └── routers/
        ├── test_auth_api.py          (8 test)
        ├── test_markalar_api.py      (4 test)
        └── test_urunler_api.py       (8 test)
```

**Güçlü Yönler:**
- 3 katmanlı test mimarisi (unit → integration → api) doğru kurulmuş
- Factory-boy ile SubFactory zinciri (Palet→Lot→Urun→Marka+Kategori) karmaşık test verisi kolaylaştırır
- Bcrypt hash cache'leme ile test performansı optimize edilmiş
- Her test öncesi TRUNCATE ile izolasyon sağlanmış
- Admin/depocu rolleri için hazır auth fixture'lar mevcut

**Zayıf Yönler:**
- `tests/integration/repositories/` dizini BOŞ — Clean Architecture repository'leri test edilmemiş
- Sadece 3 modül için API testi var (auth, markalar, urunler) — 12 router test dışı
- Factory eksiklikleri: `SiparisFactory`, `SevkiyatPlaniFactory`, `IrsaliyeFactory`, `RaporSablonuFactory` yok
- `lojistik` ve `goruntuleyen` rolleri için auth fixture yok

### 8.2 Eksik Factory'ler (Faz 2 İçin Gerekli)

| Factory | Model | Neden Gerekli |
|---------|-------|---------------|
| `SiparisFactory` | `Siparis` + `SiparisKalemi` | Sipariş CRUD testleri |
| `SevkiyatPlaniFactory` | `SevkiyatPlani` | Sevkiyat CRUD + FIFO testleri |
| `IrsaliyeFactory` | `Irsaliye` | İrsaliye CRUD testleri |
| `RaporSablonuFactory` | `RaporSablonu` | Rapor CRUD testleri |
| `StokSayimFactory` | `StokSayim` + `StokSayimKalemi` | Sayım service testleri |

---

## 9. DÜŞÜK COVERAGE MODÜL DETAY ANALİZİ

### 9.1 `crud/siparis_crud.py` — %16 Coverage (134 satır, 6 fonksiyon)

| Fonksiyon | Satır | Karmaşıklık | Test Önceliği |
|-----------|-------|-------------|---------------|
| `generate_siparis_no()` | 19 satır | Orta | Yüksek — numara çakışması riski |
| `get_siparisler()` | 18 satır | Orta | Orta — filtreleme doğruluğu |
| `get_siparis()` | 5 satır | Düşük | Düşük |
| `create_siparis()` | 40 satır | **Yüksek** | **Kritik** — KDV hesabı, kalem toplam |
| `update_siparis()` | 21 satır | Orta | Yüksek — durum geçişleri |
| `delete_siparis()` | 17 satır | Düşük | Orta — soft-delete |

**Kritik Test Senaryoları:**
- `create_siparis()`: KDV oranı ile toplam hesaplama doğruluğu
- `generate_siparis_no()`: Yıl geçişinde numara formatı (SIP-2026-0001)
- Boş kalem listesi ile sipariş oluşturma
- Eş zamanlı sipariş numarası çakışması

### 9.2 `crud/rapor_crud.py` — %17 Coverage (346 satır, 15+ fonksiyon)

**En Riskli Fonksiyonlar:**

| Fonksiyon | Satır | Karmaşıklık | Risk |
|-----------|-------|-------------|------|
| `get_abc_analiz()` | 45 satır | **Çok Yüksek** | Kümülatif yüzde algoritması, %70/%90 sınır değerleri |
| `get_depo_doluluk()` | 26 satır | **Çok Yüksek** | Subquery + COALESCE, sıfıra bölme riski |
| `get_skt_raporu()` | 17 satır | Yüksek | Tarih hesaplaması, SUM agregasyonu |
| `get_siparis_raporu_verileri()` | 18 satır | Yüksek | 3 tablo JOIN, tarih aralığı filtreleme |
| `get_stok_raporu_verileri()` | 15 satır | Yüksek | Outer JOIN doğruluğu |

### 9.3 `crud/sevkiyat_crud.py` — %19 Coverage (111 satır, 5 fonksiyon)

**Kritik:** `update_sevkiyat_plani()` (49 satır) — Durum "Yukleniyor"ye geçişte FIFO stok çıkışı tetiklenir. Hata durumunda kısmi başarı (rollback yok) riski.

### 9.4 `crud/irsaliye_crud.py` — %19 Coverage (128 satır, 5 fonksiyon)

**Kritik:** `create_irsaliye()` (55 satır) — Sevkiyat planı zaten stok çıkışı yaptıysa tekrar çıkış yapmamalı. İdempotans testi zorunlu.

### 9.5 `services/stok_sayim_service.py` — %23 Coverage (197 satır, 6 method)

| Method | Satır | Karmaşıklık | Risk |
|--------|-------|-------------|------|
| `basla()` | 40 satır | **Çok Yüksek** | Stok snapshot'ı, iç içe subquery (Lot→Palet) |
| `kalem_kaydet()` | 44 satır | **Çok Yüksek** | Upsert mantığı, durum validasyonu |
| `varyans_hesapla()` | 54 satır | **Çok Yüksek** | Fark hesaplama, yüzde, sıfıra bölme |
| `onayla()` | 13 satır | Düşük | Durum güncellemesi |

---

## 10. UYGULAMA YOLHARITASI (Detaylı)

### Adım 1: Hemen Başla — Warning Temizliği + Coverage Düzeltme

```bash
# 1. _crud_legacy.py'yi coverage'dan çıkar (veya sil)
# pytest.ini veya .coveragerc'ye ekle:
[coverage:run]
omit = _crud_legacy.py

# 2. schemas.py — 25x class Config → model_config
# 3. database.py — declarative_base import düzelt
# 4. auth.py — passlib/crypt uyumluluğunu kontrol et
```

### Adım 2: Eksik Factory'leri Oluştur

```
tests/factories/siparis_factory.py
tests/factories/sevkiyat_plani_factory.py
tests/factories/irsaliye_factory.py
tests/factories/rapor_sablonu_factory.py
tests/factories/stok_sayim_factory.py
```

### Adım 3: Basit CRUD Testleri (Hızlı Kazanım)

```
tests/integration/crud/test_kategori_crud.py    → 5 test
tests/integration/crud/test_depo_crud.py         → 5 test
tests/integration/crud/test_tedarikci_crud.py    → 5 test
tests/integration/crud/test_raf_crud.py           → 5 test
tests/integration/crud/test_marka_crud.py         → 5 test
```

### Adım 4: Kritik İş Mantığı Testleri

```
tests/integration/crud/test_siparis_crud.py       → 8-10 test
tests/integration/crud/test_sevkiyat_crud.py      → 6-8 test (FIFO!)
tests/integration/crud/test_irsaliye_crud.py      → 6-8 test (idempotans!)
tests/integration/crud/test_rapor_crud.py         → 10-12 test (ABC, doluluk)
tests/unit/services/test_stok_sayim_service.py    → 8-10 test (varyans!)
```

### Adım 5: API Router Testleri

```
tests/api/routers/test_kategoriler_api.py
tests/api/routers/test_depolar_api.py
tests/api/routers/test_lotlar_api.py
tests/api/routers/test_paletler_api.py
tests/api/routers/test_sevkiyat_api.py
tests/api/routers/test_irsaliyeler_api.py
tests/api/routers/test_raporlar_api.py
tests/api/routers/test_kullanicilar_api.py
```

### Adım 6: Clean Architecture Repository Testleri

```
tests/integration/repositories/test_sa_urun_repository.py
tests/integration/repositories/test_sa_stok_hareketi_repository.py
tests/integration/repositories/test_sa_siparis_repository.py
tests/integration/repositories/test_sa_rapor_repository.py
```

### Adım 7: CI/CD Pipeline Güçlendirme

```yaml
# .github/workflows/backend-tests.yml güncellemeleri:
- Coverage fail-under: 75%
- HTML coverage artifact upload
- pytest-xdist parallelization
- Warning → error (filterwarnings = error)
- Test stage ayrımı (unit → integration → api)
```
