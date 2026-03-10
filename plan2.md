# Raporlama Merkezi - Geliştirme Planı

> **Versiyon:** 1.0  
> **Tarih:** 10 Mart 2026  
> **Öncelik:** 🟡 Orta

---

## 1. Mimari Yapı

### Veritabanı Modelleri

```
RaporSablonu
├── id (PK)
├── ad (str) - "Aylık Stok Raporu"
├── tur (str) - "stok", "siparis", "finansal", "performans"
├── config (JSON) - { columns, filters, groupBy }
├── olusturan_kullanici_id (FK)
├── is_aktif (bool)
├── olusturma_tarihi
└── guncelleme_tarihi

RaporLogu
├── id (PK)
├── rapor_id (FK)
├── kullanici_id (FK)
├── parametreler (JSON)
├── durum (Basarili, Hatali)
├── olusturma_tarihi
└── tamamlanma_tarihi

RaporSchedule
├── id (PK)
├── sablon_id (FK)
├── periyod (str) - "gunluk", "haftalik", "aylik"
├── saat (time)
├── alici_emailler (JSON) - ["email@firm.com"]
├── format (str) - "pdf", "excel", "csv"
├── is_aktif (bool)
└── son_calistirilma
```

### API Endpoints

| Metod | Endpoint | Açıklama |
|-------|----------|-----------|
| GET/POST | `/api/raporlar/sablonlar` | Şablon yönetimi |
| POST | `/api/raporlar/olustur` | Anlık rapor oluştur |
| GET | `/api/raporlar/{tur}/veriler` | Grafik verileri |
| POST | `/api/raporlar/export` | PDF/Excel export |
| GET/POST | `/api/raporlar/schedule` | Zamanlı raporlar |
| GET | `/api/raporlar/log` | Rapor geçmişi |

---

## 2. Frontend Yapısı

### 2.1 Ana Sayfa (`/raporlar`)

**Bileşenler:**
- `RaporDashboard` - Özet kartları
- `RaporTuruSecici` - Kategori seçimi
- `RaporWidget` - Grafik/widget grid
- `SonRaporlar` - Son oluşturulan raporlar

### 2.2 Rapor Oluştur (`/raporlar/olustur`)

**Bileşenler:**
- `SablonSecici` - Hazır şablonlar
- `TarihAraligi` - Başlangıç/bitiş seçici
- `FiltrePanel` - Dinamik filtreler
- `Onizleme` - Canlı veri önizleme
- `ExportSecici` - PDF/Excel/CSV seçimi

### 2.3 Şablon Yönetimi (`/raporlar/sablonlar`)

**Bileşenler:**
- `SablonListesi` - Kayıtlı şablonlar
- `SablonEditor` - Sütun, filtre, gruplama ayarları
- `SiralamaPanel` - Sıralama kuralları

### 2.4 Zamanlı Raporlar (`/raporlar/zamanli`)

**Bileşenler:**
- `ScheduleList` - Aktif planlar
- `ScheduleForm` - Periyot, saat, e-posta ayarları
- `GecmisRaporlar` - Otomatik oluşturulanlar

---

## 3. Rapor Türleri

### 3.1 Stok Raporları
| Rapor | Açıklama |
|-------|-----------|
| Stok Durum Raporu | Mevcut stoklar, min/max seviyeler |
| Kritik Stok Raporu | Min stok altındaki ürünler |
| Stok Hareket Raporu | Giriş/çıkış hareketleri |
| SKT (Son Kullanma) Raporu | Yaklaşan son kullanma tarihleri |
| Stok Yaşlandırma | Lot bazlı yaş analizi |

### 3.2 Satış & Sipariş
| Rapor | Açıklama |
|-------|-----------|
| Sipariş Özet | Günlük/aylık siparişler |
| Ürün Bazlı Satış | Hangi ürün ne kadar satıldı |
| Müşteri Sipariş Geçmişi | Müşteri bazlı rapor |
| Sevkiyat Performansı | Teslim süreleri, başarı oranı |

### 3.3 Finansal
| Rapor | Açıklama |
|-------|-----------|
| Stok Değer Raporu | Toplam envanter değeri |
| Ürün Maliyet | Birim maliyet, kar marjı |
| Tedarikçi Borç | Ödenmesi gereken tutarlar |

### 3.4 Performans
| Rapor | Açıklama |
|-------|-----------|
| Personel Aktivite | Kullanıcı bazlı işlem sayısı |
| Depo Doluluk | Raf/depo kullanım oranları |
| İşlem Hızı | Ortalama işlem süreleri |

---

## 4. Grafik Türleri

| Grafik | Kütüphane | Kullanım Alanı |
|--------|-----------|----------------|
| Line Chart | Recharts | Trend analizi |
| Bar Chart | Recharts | Karşılaştırmalı |
| Pie/Donut | Recharts | Dağılım oranları |
| Area Chart | Recharts | Stok akışı |
| Heatmap | Plotly | Depo doluluk haritası |
| Funnel | Recharts | Sipariş dönüşümü |

---

## 5. Tasarım Kararları

### Renk Paleti
```
Primary:    #4F46E5 (Indigo-600)
Success:    #10B981 (Emerald-500)
Warning:    #F59E0B (Amber-500)
Danger:     #EF4444 (Red-500)
Background: #F8FAFC (Slate-50)
Card BG:    #FFFFFF
```

### UI Standartları
- **Border Radius:** 16px (modern kartlar)
- **Shadows:** `shadow-lg` kartlarda
- **Animations:** 200ms fade/slide
- **Icons:** Lucide React
- **Responsive:** 3 kolon (desktop), 2 (tablet), 1 (mobile)

---

## 6. Geliştirme Sırası

### Sprint 1: Altyapı
- [ ] Veritabanı modelleri
- [ ] Rapor API'leri (basic)
- [ ] Ana sayfa iskeleti

### Sprint 2: Temel Raporlar
- [ ] Stok durum raporu
- [ ] Hareket raporu
- [ ] PDF/Excel export

### Sprint 3: Görselleştirme
- [ ] Grafik widget'ları
- [ ] Dashboard özelleştirme
- [ ] Filtreleme sistemi

### Sprint 4: İleri Özellikler
- [ ] Şablon yönetimi
- [ ] Zamanlı raporlar (schedule)
- [ ] E-posta gönderimi

---

## 7. Teknoloji

| Katman | Teknoloji |
|--------|-----------|
| Charts | `recharts` (mevcut) |
| PDF | `jspdf` + `jspdf-autotable` (mevcut) |
| Excel | `xlsx` (mevcut) |
| Schedule | `node-cron` / FastAPI BackgroundTasks |
| Email | `FastAPI-Mail` |

---

## 8. Mevcut Durumdan Farklar

| Mevcut | Yeni |
|--------|------|
| Manuel export | Şablon bazlı otomatik |
| Tek sayfa | Çoklu rapor türü |
| Statik dashboard | Özelleştirilebilir widget |
| Yok | Zamanlı raporlar (e-posta) |
| Yok | Rapor loglama/tekrar |

---

## 9. Başarı Kriterleri

- [ ] 5+ hazır rapor şablonu
- [ ] PDF/Excel/CSV export
- [ ] Grafik widget entegrasyonu
- [ ] Zamanlı rapor e-posta gönderimi
- [ ] Mobil uyumlu görünüm

---

*Plan Claude Code tarafından hazırlanmıştır.*
