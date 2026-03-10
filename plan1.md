# Sevkiyat Planlama - Geliştirme Planı

> **Versiyon:** 1.0  
> **Tarih:** 10 Mart 2026  
> **Öncelik:** 🔴 Yüksek

---

## 1. Mimari Yapı

### Veritabanı Modelleri

```
Siparis (Ana Tablo)
├── id (PK)
├── siparis_no (unique)
├── musteri_id (FK - optional)
├── musteri_adi
├── teslimat_adresi
├── teslimat_tarihi
├── durum (Bekleme, Hazirlaniyor, YolaCikti, TeslimEdildi, Iptal)
├── top_miktar
├── top_tutar
├── notlar
├── olusturan_kullanici_id
├── olusturma_tarihi
├── guncelleme_tarihi
└── aktif (bool)

SiparisKalemi
├── id (PK)
├── siparis_id (FK)
├── urun_id (FK)
├── miktar
├── birim_fiyat
├── kdv_orani
└── toplam

SevkiyatPlani
├── id (PK)
├── siparis_id (FK)
├── tir_plaka
├── sofor_adi
├── sofor_telefon
├── depo_kapi
├── yukleme_tarihi
├── cikis_saati
├── varis_saati
├── durum (Planlandi, Yukleniyor, Yolda, TeslimEdildi)
└── notlar

Irsaliye
├── id (PK)
├── siparis_id (FK)
├── sevkiyat_id (FK)
├── irsaliye_no
├── irsaliye_tarihi
├── belge_turu (SevkIrsaliyesi, iadeIrsaliyesi)
├── tir_plaka
├── sofor_adi
├── durum (Taslak, Kesildi, Gonderildi)
└── pdf_url
```

### API Endpoints

| Metod | Endpoint | Açıklama |
|-------|----------|-----------|
| GET/POST | `/api/siparis/` | Sipariş listesi / oluştur |
| GET/PUT/DELETE | `/api/siparis/{id}` | Sipariş detay / güncelle |
| POST | `/api/siparis/{id}/onayla` | Siparişi sevkiyata dönüştür |
| GET/POST | `/api/sevkiyat/` | Sevkiyat planları |
| GET/POST | `/api/irsaliye/` | İrsaliye yönetimi |
| POST | `/api/irsaliye/{id}/yazdir` | PDF oluştur |
| GET | `/api/raporlar/sevkiyat` | Sevkiyat raporları |

---

## 2. Frontend Sayfa Yapısı

### 2.1 Siparişler Sayfası (`/siparisler`)

**Bileşenler:**
- `SiparisListesi` - Tablo görünümü (sıralama, filtre)
- `SiparisKart` - Kart görünümü (mobil)
- `SiparisDetayModal` - Sipariş kalemleri, durum takibi
- `YeniSiparisForm` - Çoklu ürün girişi (Dynamic Fields)
- `SiparisDurumBadge` - Renkli durum göstergesi

**Özellikler:**
- Arama (müşteri, sipariş no)
- Filtre (durum, tarih aralığı)
- Toplu işlemler (seçili sil/durdur)
- Excel export

### 2.2 Sevkiyat Planlama (`/sevkiyat-planlama`)

**Bileşenler:**
- `TakvimView` - Haftalık/aylık görünüm
- `TirListesi` - Mevcut tır/araç yönetimi
- `YuklemeSiralama` - Drag-drop ile sıralama
- `PlakaGirisi` - Plaka autocomplete
- `KapaliAlan` - Kapalı Alan Yönetimi

**Özellikler:**
- Takvim üzerinde sürükle-bırak
- Kapasite kontrolü (koli/kg)
- Çakışma uyarısı
- Araç doluluk oranı görselleştirme

### 2.3 İrsaliye Merkezi (`/irsaliyeler`)

**Bileşenler:**
- `IrsaliyeListesi` - Filtrelenebilir tablo
- `IrsaliyeOnizleme` - Gerçek zamanlı PDF önizleme
- `BarkodYazdir` - Etiket baskı widget

**Özellikler:**
- Otomatik irsaliye no üretimi (YYYY-NNNN)
- Toplu PDF oluşturma
- E-pisma gönderim
- İmza alanı (touch/signature pad)

### 2.4 Dashboard (`/sevkiyat-dashboard`)

**Widget'lar:**
- Günlük/haftalık sevkiyat sayısı
- Bekleyen siparişler
- Tır doluluk oranları
- Yaklaşan teslimatlar (timeline)

---

## 3. Tasarım Kararları

### Renk Paleti
```
Primary:    #2563EB (Blue-600)
Secondary:  #0F172A (Slate-900)
Accent:     #10B981 (Emerald-500)
Warning:    #F59E0B (Amber-500)
Danger:     #EF4444 (Red-500)
Background: #F8FAFC (Slate-50)
```

### UI Bileşen Stili
- **Border Radius:** 12px-16px (yuvarlak)
- **Shadows:** Subtle, modern (shadow-lg, shadow-xl)
- **Animations:** 200ms-300ms ease-out geçişler
- **Icons:** Lucide React (mevcut)
- **Forms:** Floating labels, inline validation

### Responsive Breakpoints
- Mobile: < 640px (tek kolon, kart view)
- Tablet: 640px - 1024px (2 kolon)
- Desktop: > 1024px (full layout)

---

## 4. Geliştirme Sırası

### Sprint 1: Temel Altyapı
- [ ] Veritabanı modelleri (Siparis, SiparisKalemi)
- [ ] CRUD API'leri
- [ ] Frontend sayfa iskeleti

### Sprint 2: Sipariş Yönetimi
- [ ] Sipariş oluşturma formu
- [ ] Liste görünümü + filtreler
- [ ] Durum güncelleme akışı

### Sprint 3: Sevkiyat Planlama
- [ ] SevkiyatPlani model + API
- [ ] Takvim entegrasyonu
- [ ] Kapasite kontrolü

### Sprint 4: İrsaliye & Rapor
- [ ] İrsaliye model + API
- [ ] PDF şablonu (mevcut kodu modernleştir)
- [ ] Excel/PDF export

---

## 5. Teknoloji & Kütüphaneler

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| PDF | `jspdf` + `jspdf-autotable` | Mevcut yapı genişletilebilir |
| Takvim | `@fullcalendar/react` | Esnek, modern |
| Drag-Drop | `@dnd-kit/core` | Erişilebilir sürükle-bırak |
| Form | `react-hook-form` + `zod` | Performanslı validation |
| Signature | `react-signature-canvas` | İrsaliye imzası |

---

## 6. Backward Compatibility

- Mevcut `StokHareketleri` çıkış kayıtları korunacak
- `siparis_no`, `tir_plaka` alanları mevcut yapıyla uyumlu
- API v2 altında yeni endpoints (`/api/v2/`)

---

## 7. Başarı Kriterleri

- [ ] Yeni sipariş oluşturma < 60 saniye
- [ ] Takvim üzerinde planlama < 30 saniye
- [ ] İrsaliye PDF oluşturma < 3 saniye
- [ ] Mobil uyumluluk testi başarılı
- [ ] 100+ sipariş performans testi

---

*Plan Claude Code tarafından hazırlanmıştır.*
