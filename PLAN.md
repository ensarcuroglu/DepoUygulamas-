# Clean Architecture Geçiş Planı — Faz 3 (Son Faz)

17/17 modül + Auth + Dashboard Clean Architecture'a taşındı. Legacy dosyalar silindi, statik doğrulama tamamlandı. **Faz 3 tamamlandı.**

## Mevcut Durum

### Tamamlanan Modüller (17/17) ✅
| # | Modül | Entity | Repo Interface | SA Repo | Use Cases | DTO | Router (CA) |
|---|-------|--------|----------------|---------|-----------|-----|-------------|
| 1 | Ürün | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2 | Stok Hareketi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 3 | Sipariş | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 4 | Marka | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 5 | Kategori | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 6 | Tedarikçi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 7 | Depo | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 8 | Raf | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 9 | Lot | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10 | Palet | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 11 | Kullanıcı | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 12 | Destek Talebi | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 13 | Sistem Log | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 14 | İrsaliye | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 15 | Sevkiyat Planlama | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 16 | Stok Sayım | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 17 | Rapor | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Ek Geçirilecekler
| Bileşen | Durum | Not |
|---------|-------|-----|
| Auth Router | ✅ | `app/api/v1/routers/auth.py`'ye taşındı — cross-cutting concern, use case gerekmedi |
| Dashboard Endpoint | ✅ | Tam CA: Repo + UseCase + DTO + Router. `main.py`'den `import crud` kaldırıldı |

---

## Scope

### In:
- ~~Kalan 4 modülün (İrsaliye, Sevkiyat, StokSayım, Rapor) Use Case + DTO + Router geçişi~~ ✅ Tamamlandı
- ~~Auth router'ın Clean Architecture'a taşınması~~ ✅ Tamamlandı
- ~~Dashboard endpoint'in ayrı router'a çıkarılması~~ ✅ Tamamlandı
- ~~DI Container'a yeni modüllerin eklenmesi~~ ✅ Tamamlandı
- ~~`main.py`'den eski router import'larının temizlenmesi~~ ✅ Tamamlandı
- Eski `crud/`, `services/`, `routers/` dosyalarının deprecated işaretlenmesi veya silinmesi

### Out:
- Frontend değişiklikleri (API endpoint'leri aynı kalacak)
- Yeni özellik eklenmesi
- Test yazımı (ayrı fazda yapılacak)
- `models.py` / `schemas.py` kaldırılması (hâlâ mapper ve auth tarafından kullanılıyor)

---

## Action Items

### Adım 1: İrsaliye Modülü (Düşük Karmaşıklık) ✅
- [x] 1.1 — `app/application/dto/irsaliye_dto.py` oluştur (Create, Update, Response, Yazdir DTO'ları)
- [x] 1.2 — `app/application/use_cases/irsaliye_use_cases.py` oluştur (Listele, Getir, Olustur, Guncelle, YazdirVerisiGetir)
- [x] 1.3 — `app/api/v1/routers/irsaliyeler.py` oluştur (DI container ile use case injection)
- [x] 1.4 — `app/infrastructure/di/container.py`'ye İrsaliye use case provider'larını ekle
- [x] 1.5 — `app/api/v1/routers/__init__.py`'ye irsaliyeler_router export'u ekle
- [x] 1.6 — `app/core/services/stok_cikis_domain_service.py` oluştur (FIFO stok çıkışı paylaşımlı domain service)

### Adım 2: Sevkiyat Planlama Modülü (Düşük Karmaşıklık) ✅
- [x] 2.1 — `app/application/dto/sevkiyat_plani_dto.py` oluştur
- [x] 2.2 — `app/application/use_cases/sevkiyat_plani_use_cases.py` oluştur (Listele, Getir, Olustur, Guncelle, Sil)
- [x] 2.3 — `app/api/v1/routers/sevkiyat_planlama.py` oluştur
- [x] 2.4 — DI container + router __init__ güncelle
- [x] 2.5 — `ISevkiyatPlaniRepository.getir_siparis_id_ile()` metodu ekle (İrsaliye stok kontrolü için)

### Adım 3: Stok Sayım Modülü (Orta Karmaşıklık) ✅
- [x] 3.1 — `app/application/dto/stok_sayim_dto.py` oluştur (Sayım + SayımKalemi + Varyans DTO'ları)
- [x] 3.2 — `app/application/use_cases/stok_sayim_use_cases.py` oluştur (Listele, Getir, Baslat, KalemKaydet, VaryansHesapla, Onayla)
- [x] 3.3 — `app/api/v1/routers/stok_sayim.py` oluştur
- [x] 3.4 — DI container + router __init__ + main.py güncelle
- [x] 3.5 — Repo interface'e `kalem_getir_by_sayim_urun()` ve `stok_snapshot_getir()` ekle + SA impl

### Adım 4: Rapor Modülü (Yüksek Karmaşıklık) ✅
- [x] 4.1 — `app/application/dto/rapor_dto.py` oluştur (Sablon, Log, Schedule, Oluşturma DTO'ları)
- [x] 4.2 — `app/application/use_cases/rapor_use_cases.py` oluştur (SablonCRUD, RaporOlustur, LogListele, ScheduleCRUD)
- [x] 4.3 — `app/api/v1/routers/raporlar.py` oluştur (303 satırlık router mantığını CA'ya taşı)
- [x] 4.4 — DI container + router __init__ güncelle

### Adım 5: Auth Router Geçişi ✅
- [x] 5.1 — `app/api/v1/routers/auth.py` oluştur (login, refresh, logout, me, register endpoint'lerini taşı)
- [x] 5.2 — `main.py`'den eski `from routers import auth` kaldırıldı, yeni CA router eklendi
- [x] 5.3 — Auth cross-cutting concern olarak kaldı; use case katmanı gerekmedi

### Adım 6: Dashboard Endpoint Taşıma ✅
- [x] 6.1 — `app/core/repositories/dashboard_repository.py` oluştur (IDashboardRepository + DashboardIstatistik value object)
- [x] 6.2 — `app/infrastructure/persistence/repositories/sa_dashboard_repository.py` oluştur
- [x] 6.3 — `app/application/dto/dashboard_dto.py` oluştur (DashboardStatsResponseDTO)
- [x] 6.4 — `app/application/use_cases/dashboard_use_cases.py` oluştur (DashboardIstatistikGetirUseCase)
- [x] 6.5 — `app/api/v1/routers/dashboard.py` oluştur
- [x] 6.6 — DI container'a dashboard repo factory + use case factory eklendi
- [x] 6.7 — `main.py`'den inline dashboard endpoint, `import crud`, `DashboardStats` import'u kaldırıldı

### Adım 7: main.py Temizliği ✅ (Adım 5+6 ile birlikte yapıldı)
- [x] 7.1 — Eski `from routers import ...` satırları kaldırıldı
- [x] 7.2 — Tüm CA router'lar import/include edildi
- [x] 7.3 — `main.py`'de sadece app setup, middleware, lifespan, exception handler ve APScheduler kaldı

### Adım 8: Legacy Dosya Temizliği ✅
- [x] 8.1 — `routers/` klasörü tamamen silindi (17 dosya — tüm eski router'lar CA'ya taşınmıştı)
- [x] 8.2 — `services/` klasörü tamamen silindi (14 dosya — iş mantığı use case'lere taşınmıştı)
- [x] 8.3 — `crud/` klasörü tamamen silindi (16 dosya — sorgu mantığı repository'lere taşınmıştı)
- [x] 8.4 — `_crud_legacy.py` silindi (hiçbir yerde import edilmiyordu)
- [x] 8.5 — `tests/integration/crud/` ve `tests/integration/services/` eski testleri silindi (legacy kodu test ediyorlardı)

### Adım 9: Doğrulama ✅
- [x] 9.1 — Python import zinciri doğrulaması: tüm `.py` dosyaları AST ile tarandı, kırık import yok
- [x] 9.2 — Silinen modüllere (`crud/`, `services/`, `routers/`) referans taraması: sıfır kırık import (app + test)
- [x] 9.3 — Pytest: MySQL bağımlılığı nedeniyle çalıştırılamadı (pre-existing — `conftest.py` → `main.py` → `Base.metadata.create_all`). Statik analiz ile doğrulandı
- **Not:** Tam runtime doğrulama MySQL bağlantısı ile yapılmalıdır (`uvicorn main:app --reload`)

---

## Tahmini İş Sırası ve Öncelik

```
Faz 3a (Basit modüller):  Adım 1 + Adım 2  → İrsaliye + Sevkiyat           ✅ Tamamlandı
Faz 3b (Orta modül):      Adım 3            → Stok Sayım                   ✅ Tamamlandı
Faz 3c (Karmaşık modül):  Adım 4            → Rapor                        ✅ Tamamlandı
Faz 3d (Cross-cutting):   Adım 5 + Adım 6 + Adım 7 → Auth + Dashboard + main.py  ✅ Tamamlandı
Faz 3e (Temizlik):        Adım 8             → legacy silme                 ✅ Tamamlandı
Faz 3f (Doğrulama):       Adım 9             → test + doğrulama             ✅ Tamamlandı (statik analiz)
```

## Referans: Bir Modülün CA Katman Yapısı

Her modül için oluşturulacak dosyalar:
```
app/
├── application/
│   ├── dto/{modul}_dto.py              # Pydantic DTO'lar (Create, Update, Response)
│   └── use_cases/{modul}_use_cases.py  # İş mantığı Use Case sınıfları
├── api/v1/routers/{modul}.py           # FastAPI router (DI ile use case injection)
└── infrastructure/di/container.py       # get_{modul}_{aksiyon}_uc fonksiyonları eklenir
```

Zaten mevcut olan katmanlar (dokunulmayacak):
```
app/
├── core/
│   ├── entities/{modul}.py             # ✅ Domain entity (dataclass)
│   └── repositories/{modul}_repository.py  # ✅ Abstract repository interface
└── infrastructure/persistence/
    ├── repositories/sa_{modul}_repository.py  # ✅ SQLAlchemy implementasyonu
    └── mappers.py                              # ✅ Entity ↔ ORM mapping
```

---

## Open Questions

1. **`models.py` ve `schemas.py` ne zaman kaldırılacak?** — Mapper'lar ve auth hâlâ bunlara bağımlı. Tam kaldırma için ayrı bir refactoring fazı gerekiyor.
2. ~~**Eski `crud/__init__.py` main.py'de hâlâ import ediliyor**~~ ✅ Çözüldü — Dashboard taşındıktan sonra `import crud` satırı kaldırıldı.
3. **APScheduler `main.py`'de inline** — Zamanlı rapor tetikleme mantığı bir servis/use case'e mi taşınmalı, yoksa infrastructure concern olarak mı kalmalı?
