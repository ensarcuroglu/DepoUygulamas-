# Depo Yönetim Sistemi - Detaylı Teknik Analiz & Action Plan

**Tarih:** 12 Mart 2026  
**Analiz Düzeyi:** Kod incelemesi + Mimari değerlendirme  

---

## 📊 I. MEVCUT DURUM ÖZETİ

### ✅ Güçlü Yönler

| Alan | Değerlendirme | Detay |
|------|---------------|-------|
| **Auth Sistem** | ⭐⭐⭐⭐⭐ | JWT + Refresh Token, bcrypt hashing, güçlü secret key validation |
| **DB Tasarımı** | ⭐⭐⭐⭐⭐ | İyi normalized schema, ilişkiler doğru, lot/palet tracking |
| **API Interceptors** | ⭐⭐⭐⭐ | Request/response interceptors, automatic retry, queue management |
| **Role-Based Access** | ⭐⭐⭐⭐⭐ | `require_role()` factory, PoLP (Principle of Least Privilege) uygulanmış |
| **APScheduler** | ⭐⭐⭐⭐ | Zamanlı raporlar, e-posta bildirimleri otomasyonu yapılmış |
| **UI/UX** | ⭐⭐⭐⭐ | Tailwind CSS, responsive tasarım, barkod tarayıcı (ZXing) |

### ⚠️ Zayıf Yönler & Eksiklikler

| Alan | Durum | Etki |
|------|-------|------|
| **Test Coverage** | ❌ Yok | Refactoring ve feature eklemede risk yüksek |
| **Stok Sayım Modülü** | ❌ Yok | Periyodik inventar denetilemez — stok doğruluk sorunu |
| **WebSocket Desteği** | ❌ Yok | Anlık güncellemeler yok; polling gerekliliği |
| **Redis Caching** | ❌ Yok | Dashboard slow, DB overload riski |
| **TypeScript** | ❌ Yok | Frontend'de type safety yok, IDE support zayıf |
| **Entegrasyon APIs** | ❌ Yok | e-Fatura, Kargo, e-Ticaret bağlantısı yok |
| **AI/ML Modelleri** | ❌ Yok | Stok tahmini, anomali tespiti, otomatik sipariş önerisi yok |
| **Monitoring & Logging** | ⚠️ Eksik | SistemLog tablosu var ama centralized monitoring yok |
| **Documentation** | ⚠️ Eksik | API dokümantasyonu Swagger'da otomatik ama domain logic dokümantasyonu yok |

---

## 📋 II. TEKNIK BORÇ (Technical Debt) - İŞ İTEM LİSTESİ

### 1️⃣ **Critical Priority** (Hafta 1-2)

#### 1.1 Stok Sayım Modülü (Inventar)
```
Status: ❌ Yapılmamış
Impact: Stok doğruluğu garantisi yok

Gereksin:
- Model: StokSayim, StokSayimKalemi
- Router: stok_sayim_kalplari
- Frontend: StokSayimPage.jsx
- İşem:
  1. Sayım şablonu oluştur (başlangıç stok snapshot'ı)
  2. QR/barkod ile sayım veri girdisi
  3. Varyans raporlaması (sayım farkları)
  4. Otomatik stok düzeltmesi

Est. Time: 5-7 gün
```

#### 1.2 Test Infrastructure Kuruyla
```
Status: ❌ Yok
Impact: Refactoring yapılamaz, bug regression riski yüksek

Yapılacak:
- pytest + pytest-asyncio Backend
- test_auth.py (JWT, refresh token)
- test_crud.py (DB operations, FIFO logic)
- test_urunler.py (ürün CRUD, stok hesaplama)
- Frontend: Vitest setup + component tests

Est. Time: 3-5 gün
```

#### 1.3 Database Performance Tuning
```
Status: ⚠️ Başlanmış (Indeks var mı kontrol et)
Impact: Large dataset'lerde (100K+ stok hareketi) slow queries

Yapılacak:
1. MySQL indekseri ekle:
   - stok_hareketleri: (urun_id, tarih)
   - paletler: (aktif, lot_id)
   - lots: (aktif, son_kullanma_tarihi)

2. Materialized View oluştur:
   - v_urun_stok_miktari (Urun + toplam Palet.koli_adedi)
   - v_raf_doluluk (Raf kullanım %)

3. Slow Query Logging aktifleştir (.env)

Est. Time: 2-3 gün
```

### 2️⃣ **High Priority** (Hafta 3-4)

#### 2.1 Redis Caching Layer
```
Status: ❌ Yok
Impact: Dashboard slow (kompleks istatistik sorguları)

Yapılacak:
- redis-py entegrasyonu
- Cache keys:
  * "dashboard:stats" (5 min TTL)
  * "urun:list:{page}" (15 min TTL)
  * "depo:{id}:raflar" (1 hour TTL)
- Cache invalidation stratejisi (INSERT/UPDATE/DELETE → flush relevant keys)

Est. Time: 4-5 gün
```

#### 2.2 WebSocket Layer (Real-time Updates)
```
Status: ❌ Yok  
Impact: Çoklu kullanıcı aynı anda çalışırken stok senkronizasyon yok

Yapılacak:
- fastapi-socketio veya websockets
- broadcast topics:
  * stock_update: {urun_id, yeni_stok, varsa_palet_id}
  * lot_closed: {lot_id, palet_listesi}
  * user_activity: {user_id, action}
- Frontend: useSocket hook

Est. Time: 5-7 gün
```

#### 2.3 TypeScript Migration (Frontend)
```
Status: ❌ Yok
Impact: Type safety yok, IDE autocomplete zayıf, re-factory riski

Yapılacak:
- tsconfig.json, eslint + typescript rules
- Gradual migration: App.jsx → contexts → hooks → pages
- API response types (api.d.ts)

Est. Time: 7-10 gün (gradual)
```

### 3️⃣ **Medium Priority** (Ay 2)

#### 3.1 Anomali Tespiti (AI)
```
Status: ❌ Yok
Alg: Isolation Forest / Local Outlier Factor

Veri: Stok hareketleri (qtty, timestamp, user)
Tetikleyiciler:
- Aynı üründe >10x normal çıkış miktarı
- Beklenmedik ürün kombinasyonları
- Off-hours activity

Output: Dashboard alert + SistemLog entry

Est. Time: 4-5 gün (scikit-learn)
```

#### 3.2 Demand Forecasting (AI)
```
Status: ❌ Yok
Model: Prophet veya LSTM

Input: Son 3 ay stok çıkış hareketleri
Output: 
- 7 gün tahmin (güven aralığı)
- Reorder Point önerisi
- Kritik stok uyarısı

Est. Time: 6-8 gün
```

### 4️⃣ **Low Priority** (Ay 3+)

#### 4.1 Entegrasyon (e-Fatura, Kargo, vb)
```
Yapılacak:
- e-Fatura (UBL-TR): Invoice model, e-invoice endpoint
- Kargo APIs: Aras, Sürat, Yurtiçi wrapper servisleri
- e-Ticaret: WooCommerce API sync

Est. Time: 2-3 hafta (integration by integration)
```

#### 4.2 Mobil App (Wrapper)
```
Yapılacak:
- Ionic/Capacitor wrapping
- Push notifications
- Offline sync (Ampersand)
- Camera optimization

Est. Time: 3-4 hafta
```

---

## 🚀 III. FEATURE GAP ANALYSIS

### Eksik ama Raporda Önerilen Özellikler

| Özellik | Model | Router | Frontend | Status |
|---------|-------|--------|----------|--------|
| **Stok Sayım** | ❌ | ❌ | ❌ | ❌ |
| **Sarf Malzemeleri** | ❌ | ❌ | ❌ | ❌ |
| **Filo Yönetimi** | ❌ | ❌ | ❌ | ❌ |
| **Müşteri Portalı** | ❌ | ❌ | ❌ | ❌ |
| **Anomali Tespiti** | ❌ | ❌ (API var) | ❌ | ⚠️ |
| **AI Stok Tahmini** | ❌ | ❌ (API var) | ❌ | ⚠️ |

---

## 📈 IV. PERFORMANCE & SECURITY AUDIT

### Performance Bottlenecks

| Alan | Sorun | Çözüm |
|------|-------|-------|
| Dashboard Stats | N+1 queries | Redis cache + JOIN optimize |
| Ürün Listesi > 10K | No pagination | `offset/limit` + infinite scroll |
| Stok Hareketi Export | In-memory → timeout | Async task queue (Celery) + file download |
| Barkod Scan (Bulk) | Sequential requests | Batch endpoint `/api/urunler/batch-lookup` |

### Security Notes

| Madde | Status | Not |
|------|--------|-----|
| JWT Secret Rotation | ⚠️ | Her 90 gün rotate et |
| 2FA (İki Faktörlü) | ❌ | TOTP (Google Authenticator) ekle |
| Rate Limiting | ✅ | slowapi kullanılıyor |
| API Key Support | ❌ | Harici sistemler için ekle |
| CORS | ✅ | Frontend URL'ler allow-listed |
| SQL Injection | ✅ | ORM (SQLAlchemy) kullanılıyor |
| Sensitive Data Logs | ⚠️ | Şifre/token loglanmaması kontrol et |

---

## 🎯 V. GELIŞTIRME ROADMAP (6 AY)

### **Faz 1: Temel Stabilite (Hafta 1-4)**
- ✅ Stok Sayım modülü
- ✅ Test infrastructure
- ✅ Database tuning
- ✅ Monitoring dashboard

**Expected Outcome:** Stok doğruluğu garantisi + stable codebase

### **Faz 2: Real-time & Caching (Hafta 5-8)**
- ✅ Redis caching
- ✅ WebSocket desteği
- ✅ TypeScript migration start

**Expected Outcome:** <1s page load, real-time updates, type safety

### **Faz 3: AI & Intelligence (Hafta 9-16)**
- ✅ Anomali tespiti
- ✅ Demand forecasting
- ✅ Otomatik sipariş önerisi

**Expected Outcome:** Proactive stok yönetimi, fire azalması

### **Faz 4: Entegrasyon (Hafta 17-24)**
- ✅ e-Fatura/e-İrsaliye
- ✅ Kargo APIs
- ✅ e-Ticaret sync

**Expected Outcome:** System interoperability, order to delivery automation

### **Faz 5: Ölçek & Polish (Hafta 25+)**
- ✅ Mobil app (Ionic wrapper)
- ✅ Müşteri portalı
- ✅ BI raporlama (dashboard widgets)

---

## 📋 VI. HAFTALIK SPRINT TASK TEMPLATE

### Sprint Week 1-2: Stok Sayım + Tests
```
Frontend Tasks:
- [ ] StokSayimPage.jsx (barkod scan UI)
- [ ] sayim-form component
- [ ] varyans raporu görselleştirmesi

Backend Tasks:
- [ ] models.py: StokSayim, StokSayimKalemi
- [ ] routers/stok_sayim.py (CRUD + sayım kapatma logic)
- [ ] crud.py: hesapla_varyans(), onayla_sayim()
- [ ] seed.py'ye örnek sayım ekle

Test Tasks:
- [ ] test_sayim_crud.py
- [ ] test_sayim_varyans_hesaplama.py
- [ ] test integration: StokHareketi generator
```

---

## 🔧 VII. ÖNERIYLE DEĞİŞKEN KILAVUZU

### Backend'e Eklenecek Dependencies
```
# requirements.txt
redis==5.0.1
fastapi-socketio==0.0.10
python-socketio==5.10.0
scikit-learn==1.3.2  # Anomali tespiti
fbprophet==0.7.10   # Demand forecasting (çift kontrol edin)
celery==5.3.4       # Background tasks
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Frontend'e Eklenecek Dependencies
```
# package.json
"typescript": "^5.3.3"
"socket.io-client": "^4.7.2"
```

---

## 💡 VIII. QUICK WINS (Bu Haftaya)

Hızlı değer sağlayacak, minimum effort işler:

| İş | Est. Time | Impact |
|-----|-----------|--------|
| MySQL indeks ekle (stok_hareketleri.urun_id, paletler.aktif) | 30 min | 2x query speed |
| Dashboard page size limit'i 100 → 50 | 10 min | Memory 40% azalma |
| Kullanıcı session timeout'u 8 hour → 4 hour | 5 min | Security improvement |
| API error messages standardize et | 1 hour | Better debugging |
| "Ürünler" sayfasına "Stok Seviyesi" filtesi ekle | 2 hours | UX improvement |

---

## 🎓 IX. DOCUMENTATION CHECKLIST

Yapılması gereken dokümantasyon:

- [ ] **API Schema** — OpenAPI enhancements (description fields)
- [ ] **Database Diagram** — ER diagram (draw.io)
- [ ] **Architecture Document** — System design, data flow
- [ ] **Deployment Guide** — Docker Compose, production checklist
- [ ] **Security Policy** — Güvenlik best practices
- [ ] **Contributing Guide** — Code standards, PR process

---

## 📞 X. STAKEHOLDER RECOMMENDATIONS

**Müdüre Bilgi Sunuş:**

> **Pozitif:** Sistem iyi temel üzerine kurulmuş, core features stabil.  
> **Risk:** Stok doğruluğu (Sayım modülü yok), performans (cache yok), type safety (JS tests yok).  
> **Yol Haritası:** 6 ay içinde AI-powered stok optimizasyonu + entegrasyon ekle → ROI 40% artır.

---

*Son Güncelleme: 12 Mart 2026*
