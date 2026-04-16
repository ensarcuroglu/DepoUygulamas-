# Firma İçi Üretim Paleti Giriş Sistemi - Analiz ve Çözüm Raporu

**Özet:** Mevcut palet giriş yapısı harici kaynaklara (ERP/İrsaliye) bağımlıdır; firma içi üretim paletleri için yeni bir "iç kaynak" adaptörü ve oto-artan seri numaralı etiket sistemi gereklidir.

---

## 1. Mevcut Sistem Analizi

### 1.1. Var Olan Yapı

| Bileşen | Konum | Görevi |
|---------|-------|--------|
| `IPaletVeriKaynagiService` | `@BackendProje/app/core/services/palet_veri_kaynagi_service.py:14-43` | Soyut adaptör arayüzü |
| `IrsaliyePaletVeriKaynagiService` | `@BackendProje/app/infrastructure/services/irsaliye_palet_veri_kaynagi_service.py:24-137` | İrsaliye tabanlı kaynak |
| `ErpPaletVeriKaynagiService` | `@BackendProje/app/infrastructure/services/erp_palet_veri_kaynagi_service.py:27-196` | ERP API adaptörü (henüz aktif değil) |
| `PaletGirisService` | `@BackendProje/app/core/services/palet_giris_service.py:30-220` | Ana domain servisi |
| `PaletBilgiDTO` | `@BackendProje/app/application/dto/palet_bilgi_dto.py:18-39` | Kaynak-bağımsız veri transfer objesi |
| `PaletKaynak` | `@BackendProje/app/application/dto/palet_bilgi_dto.py:15` | `"irsaliye" \| "erp" \| "sistem"` literal tipi |

### 1.2. Mevcut Giriş Akışı (İrsaliye Kaynaklı)

```
┌─────────────────────────────────────────────────────────────────┐
│  ADIM 1: Palet No Tarama (Frontend)                              │
│  ↓                                                               │
│  ADIM 2: IPaletVeriKaynagiService.palet_bilgisi_getir(palet_no)  │
│  ↓                                                               │
│  ADIM 3: Kaynak → PaletBilgiDTO dönüşümü                          │
│  ↓                                                               │
│  ADIM 4: PaletGirisService.palet_giris() iş kuralları             │
│  ↓                                                               │
│  ADIM 5: Kaynak onaylama (giris_yapildi_mi = true)               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3. Mevcut Sistemdeki Eksiklikler (Üretim Paleti İçin)

| Eksiklik | Açıklama | Risk Seviyesi |
|----------|----------|---------------|
| **Kaynak Tipi Yok** | `PaletKaynak` literalinde `"uretim"` yok | 🔴 Yüksek |
| **Veri Kaynağı Yok** | Üretim paletleri için veri kaynağı adaptörü yok | 🔴 Yüksek |
| **Etiket Üretimi Yok** | Oto-artan PRD-XXX formatında seri numara üretimi yok | 🟡 Orta |
| **Lot Stratejisi Belirsiz** | Üretim lotları için endüstri standardı belirlenmemiş | 🟡 Orta |
| **Raf Atama** | Üretim paletleri için özel raf/konum stratejisi yok | 🟢 Düşük |

---

## 2. Endüstri Standartları Analizi

### 2.1. Üretim Paleti Etiketleme Standartları

| Standart | Format | Kullanım Alanı |
|----------|--------|----------------|
| **GS1-128 (SSCC)** | `(00)123456789012345678` | Küresel tedarik zinciri |
| **AIAG** (Otomotiv) | `MFG-YYMMDD-SEQ` | OEM üreticiler |
| **İlaç/Farma** | `LOT+SKT+SEQ` | FDA/EMA uyumlu |
| **Gıda** | `ÜRETİM_TARİHİ+SAAT+SHIFT` | GFSI/BRC uyumlu |

### 2.2. Önerilen Format (PRD-YYYYMMDD-XXX)

**Format:** `PRD-YYYYMMDD-NNNN`

| Segment | Açıklama | Örnek |
|---------|----------|-------|
| `PRD` | Üretim (Production) sabit prefix | `PRD` |
| `YYYYMMDD` | Üretim tarihi (ISO 8601) | `20250416` |
| `NNNN` | Gün içi oto-artan 4 haneli seri | `0001-9999` |

**Örnek:** `PRD-20250416-0001`, `PRD-20250416-0042`

### 2.3. Lot Numarası Standartları

| Yaklaşım | Format | Avantaj | Dezavantaj |
|----------|--------|---------|------------|
| **Tarih Bazlı** | `LOT-YYYYMMDD-VV` (V=vardiya) | Basit, takip kolay | Gün içi çoklu üretim için yetersiz |
| **Üretim Emri Bazlı** | `EMR-XXXXX-REV` | ERP entegrasyonu kolay | Manuel emri takibi gerekir |
| **Hibrit** | `LOT-YYYYMMDD-EMRXX-VV` | En kapsamlı | Daha uzun, karmaşık |

**Öneri:** `LOT-YYYYMMDD-XXX-V` formatı (Örn: `LOT-20250416-001-A`)

---

## 3. Çözüm Mimarisi

### 3.1. Yeni Bileşenler

```
┌──────────────────────────────────────────────────────────────────────┐
│                    ÜRETİM PALETİ GİRİŞ MİMARİSİ                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐      ┌──────────────────────┐               │
│  │ UretimPaletService   │      │ UretimPaletRepository │               │
│  │ (Domain Service)     │      │ (Repository Pattern)  │               │
│  └──────────┬───────────┘      └──────────┬───────────┘               │
│             │                              │                          │
│             ▼                              ▼                          │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │      IUretimPaletVeriKaynagiService (Yeni Adaptör)           │     │
│  │         ↓ İmplements IPaletVeriKaynagiService               │     │
│  └────────────────────────────────────────────────────────────┘     │
│             │                                                          │
│             ▼                                                          │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │   UretimPaletKaynagiService (Concrete Adapter)              │     │
│  │   • Yerel DB'den okur / yazar                               │     │
│  │   • Oto-artan seri numara üretir                            │     │
│  │   • Lot numarası otomatik oluşturur                         │     │
│  └────────────────────────────────────────────────────────────┘     │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2. Değişiklik Gereken Dosyalar

| Dosya | Değişiklik Tipi | Satırlar |
|-------|-----------------|----------|
| `palet_bilgi_dto.py` | `PaletKaynak` literal genişletme | ~1 satır |
| `palet_veri_kaynagi_service.py` | Yeni adaptör implementasyonu | ~150 satır |
| `stok_islemleri.py` | Kaynak tipi routing | ~20 satır |
| `UretimPalet` entity/model | Yeni model | ~50 satır |
| `StokHareketleriPage.jsx` | UI kaynak gösterimi | ~10 satır |

### 3.3. Veritabanı Şeması (Önerilen)

```sql
-- Üretim Paletleri Tablosu
CREATE TABLE uretim_paletleri (
    id SERIAL PRIMARY KEY,
    palet_no VARCHAR(20) UNIQUE NOT NULL,  -- PRD-YYYYMMDD-NNNN
    urun_id INTEGER REFERENCES urunler(id),
    lot_no VARCHAR(30),                      -- LOT-YYYYMMDD-NNNN-V
    miktar INTEGER NOT NULL,
    depo_id INTEGER REFERENCES depolar(id),
    raf_id INTEGER REFERENCES raflar(id) NULL,
    uretim_tarihi DATE NOT NULL DEFAULT CURRENT_DATE,
    vardiya CHAR(1),                         -- A, B, C
    uretim_emri_no VARCHAR(20),              -- Opsiyonel
    giris_yapildi_mi BOOLEAN DEFAULT FALSE,
    olusturma_tarihi TIMESTAMP DEFAULT NOW(),
    guncelleme_tarihi TIMESTAMP DEFAULT NOW()
);

-- Seri Numara Sayaç Tablosu
CREATE TABLE uretim_seri_sayac (
    tarih DATE PRIMARY KEY,
    son_seri_no INTEGER DEFAULT 0
);
```

---

## 4. Implementasyon Planı

### 4.1. Faz 1: Çekirdek Yapı (1-2 gün)

| Görev | Dosya | Öncelik |
|-------|-------|---------|
| 1.1. `PaletKaynak` genişletme | `palet_bilgi_dto.py:15` | 🔴 Yüksek |
| 1.2. `UretimPaletKaynagiService` adaptörü | Yeni dosya | 🔴 Yüksek |
| 1.3. `UretimPaletRepository` | Yeni dosya | 🔴 Yüksek |
| 1.4. `IUretimPaletVeriKaynagiService` arayüzü | Yeni dosya | 🔴 Yüksek |

### 4.2. Faz 2: İş Kuralları (1 gün)

| Görev | Açıklama |
|-------|----------|
| 2.1. Seri numara üretimi | `PRD-YYYYMMDD-NNNN` formatında atomic sayaç |
| 2.2. Lot numarası stratejisi | `LOT-YYYYMMDD-NNNN-V` otomatik oluşturma |
| 2.3. Raf atama | Mevcut STAGING rafı veya yeni ÜRETIM_ALANI rafı |
| 2.4. Validasyon | Çift giriş kontrolü, depo yetkisi |

### 4.3. Faz 3: API ve Frontend (1-2 gün)

| Görev | Endpoint/Dosya |
|-------|----------------|
| 3.1. Üretim paleti oluşturma API | `POST /api/v1/uretim-paletleri` |
| 3.2. Kaynak bazlı routing | `stok_islemleri.py` adaptör seçimi |
| 3.3. UI kaynak gösterimi | `StokHareketleriPage.jsx:521-527` |
| 3.4. Etiket baskı entegrasyonu | Zebra yazıcı template (opsiyonel) |

---

## 5. Riskler ve Öneriler

### 5.1. Teknik Riskler

| Risk | Olasılık | Etki | Önlem |
|------|----------|------|-------|
| Seri numara çakışması | Düşük | Yüksek | DB-level UNIQUE constraint + transaction |
| Çoklu kullanıcı race condition | Orta | Orta | `SELECT FOR UPDATE` ile sayaç |
| Kaynak tipi karışıklığı | Orta | Orta | `PaletBilgiDTO.kaynak` validasyonu |

### 5.2. İş Süreci Riskleri

| Risk | Önlem |
|------|-------|
| Depo personeli üretim verisi giremiyor | Aynı `depocu` rolü kullanılabilir |
| Üretim/depo koordinasyonu | Üretim paleti "beklemede" durum konsepti |

---

## 6. Sonuç ve Öneriler

### 6.1. Uyumluluk Durumu

**Mevcut Yapı:** 🔴 **Doğrudan uyumlu DEĞİL**

- Harici kaynak bağımlılığı var
- Üretim kaynağı için adaptör yok
- Etiket üretim mekanizması yok

### 6.2. Önerilen Yol Haritası

```
┌────────────────────────────────────────────────────────────┐
│  HAFTA 1: Çekirdek Implementasyon                           │
│  ├── Faz 1: Model + Repository + Adaptör (2 gün)           │
│  ├── Faz 2: İş kuralları + validasyon (1 gün)              │
│  └── Faz 3: API + Frontend entegrasyon (2 gün)             │
├────────────────────────────────────────────────────────────┤
│  HAFTA 2: Test ve İyileştirme                              │
│  ├── Unit testler (1 gün)                                  │
│  ├── Entegrasyon testi (1 gün)                             │
│  └── Etiket baskı entegrasyonu (opsiyonel, 2 gün)         │
└────────────────────────────────────────────────────────────┘
```

### 6.3. Hızlı Başlangıç (MVP)

En hızlı implementasyon için önerilen sıra:

1. **Önce:** `PaletKaynak` literaline `"uretim"` ekle
2. **Sonra:** `UretimPaletKaynagiService` adaptörünü oluştur (mevcut `IPaletVeriKaynagiService`'den türet)
3. **En Son:** `PaletGirisService`'e kaynak bazlı routing ekle

---

## 7. Ek Notlar

- **Depo Personeli:** Mevcut `depocu` rolü üretim paleti girişi yapabilir, ayrı rol gerekmez
- **Etiket Formatı:** `PRD-` prefix'i ileride değiştirilebilir (konfigürasyon tabanlı yapılabilir)
- **Lot Stratejisi:** Tarih+basıç sayaç+vardiya kombinasyonu endüstride yaygın kullanılır
- **Raf Atama:** Mevcut STAGING rafı kullanılabilir veya üretim için özel raf tipi tanımlanabilir

---

*Rapor Tarihi: 16 Nisan 2025*
*Analiz Kapsamı: Backend + Frontend palet giriş modülleri*
