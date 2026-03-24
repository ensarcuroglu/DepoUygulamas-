# Clean Architecture Geçiş Planı — Faz 3 (Son Faz)

13/17 modül Clean Architecture'a taşındı (%76). Bu plan kalan 4 modülü + auth router + dashboard endpoint'i migrate ederek geçişi tamamlar.

## Mevcut Durum

### Tamamlanan Modüller (13/17) ✅
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

### Kalan Modüller (4/17) ❌
| # | Modül | Entity | Repo Interface | SA Repo | Use Cases | DTO | Router (CA) | Karmaşıklık |
|---|-------|--------|----------------|---------|-----------|-----|-------------|-------------|
| 14 | İrsaliye | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Düşük (61 satır router, 90+127 service/crud) |
| 15 | Sevkiyat Planlama | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Düşük (66 satır router, 49+110 service/crud) |
| 16 | Stok Sayım | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Orta (70 satır router, 196 service) |
| 17 | Rapor | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | Yüksek (303 satır router, 189+345 service/crud) |

### Ek Geçirilecekler
| Bileşen | Durum | Not |
|---------|-------|-----|
| Auth Router | ❌ | 223 satır, eski `routers/auth.py`'de — JWT login/register/me |
| Dashboard Endpoint | ❌ | `main.py` içinde inline, `crud.get_dashboard_stats` kullanıyor (28 satır) |

---

## Scope

### In:
- Kalan 4 modülün (İrsaliye, Sevkiyat, StokSayım, Rapor) Use Case + DTO + Router geçişi
- Auth router'ın Clean Architecture'a taşınması
- Dashboard endpoint'in ayrı router'a çıkarılması
- DI Container'a yeni modüllerin eklenmesi
- `main.py`'den eski router import'larının temizlenmesi
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

### Adım 3: Stok Sayım Modülü (Orta Karmaşıklık)
- [ ] 3.1 — `app/application/dto/stok_sayim_dto.py` oluştur (Sayım + SayımKalemi DTO'ları)
- [ ] 3.2 — `app/application/use_cases/stok_sayim_use_cases.py` oluştur (Listele, Getir, Olustur, Baslat, Bitir, Onayla, KalemEkle, Fark)
- [ ] 3.3 — `app/api/v1/routers/stok_sayim.py` oluştur
- [ ] 3.4 — DI container + router __init__ güncelle

### Adım 4: Rapor Modülü (Yüksek Karmaşıklık)
- [ ] 4.1 — `app/application/dto/rapor_dto.py` oluştur (Sablon, Log, Schedule, Oluşturma DTO'ları)
- [ ] 4.2 — `app/application/use_cases/rapor_use_cases.py` oluştur (SablonCRUD, RaporOlustur, LogListele, ScheduleCRUD)
- [ ] 4.3 — `app/api/v1/routers/raporlar.py` oluştur (303 satırlık router mantığını CA'ya taşı)
- [ ] 4.4 — DI container + router __init__ güncelle

### Adım 5: Auth Router Geçişi
- [ ] 5.1 — `app/api/v1/routers/auth.py` oluştur (login, register, me endpoint'lerini taşı)
- [ ] 5.2 — Auth iş mantığını mevcut `auth.py` modülünden use case'e çevirmeye **gerek yok** — auth cross-cutting concern olarak kalabilir; sadece router lokasyonu değişir

### Adım 6: Dashboard Endpoint Taşıma
- [ ] 6.1 — `app/application/use_cases/dashboard_use_cases.py` oluştur (GetDashboardStats)
- [ ] 6.2 — `app/application/dto/dashboard_dto.py` oluştur
- [ ] 6.3 — `app/api/v1/routers/dashboard.py` oluştur
- [ ] 6.4 — `main.py`'deki inline dashboard endpoint'i kaldır

### Adım 7: main.py Temizliği
- [ ] 7.1 — Eski `from routers import ...` satırlarını kaldır
- [ ] 7.2 — Yeni CA router'ların import/include'larını ekle
- [ ] 7.3 — `main.py`'de sadece app setup, middleware, lifespan ve exception handler kalacak şekilde sadeleştir

### Adım 8: Legacy Dosya Temizliği
- [ ] 8.1 — Eski `routers/` klasöründeki taşınan dosyaları sil (auth, irsaliyeler, raporlar, sevkiyat_planlama, stok_sayim)
- [ ] 8.2 — Eski `services/` klasöründeki karşılık gelen service dosyalarını sil (irsaliye_service, rapor_service, sevkiyat_service, stok_sayim_service)
- [ ] 8.3 — Eski `crud/` klasöründeki karşılık gelen dosyaları sil (irsaliye_crud, rapor_crud, sevkiyat_crud, dashboard_crud)
- [ ] 8.4 — `routers/__init__.py`, `services/__init__.py`, `crud/__init__.py` export'larını güncelle

### Adım 9: Doğrulama
- [ ] 9.1 — `uvicorn main:app` ile sunucuyu başlat, tüm endpoint'lerin `/docs`'ta göründüğünü doğrula
- [ ] 9.2 — Her modül için temel CRUD işlemlerini Swagger UI üzerinden test et
- [ ] 9.3 — Mevcut testleri çalıştır: `cd BackendProje && python -m pytest`

---

## Tahmini İş Sırası ve Öncelik

```
Faz 3a (Basit modüller):  Adım 1 + Adım 2  → İrsaliye + Sevkiyat
Faz 3b (Orta modül):      Adım 3            → Stok Sayım
Faz 3c (Karmaşık modül):  Adım 4            → Rapor
Faz 3d (Cross-cutting):   Adım 5 + Adım 6   → Auth + Dashboard
Faz 3e (Temizlik):        Adım 7 + Adım 8 + Adım 9 → main.py + legacy silme + doğrulama
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
2. **Eski `crud/__init__.py` main.py'de hâlâ import ediliyor** — Dashboard taşındıktan sonra `import crud` satırı silinebilir mi, yoksa başka bağımlılıklar var mı kontrol edilmeli.
3. **APScheduler `main.py`'de inline** — Zamanlı rapor tetikleme mantığı bir servis/use case'e mi taşınmalı, yoksa infrastructure concern olarak mı kalmalı?
