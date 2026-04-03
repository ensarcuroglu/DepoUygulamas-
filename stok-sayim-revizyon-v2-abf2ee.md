# Stok Sayım Sayfası - Revizyon Planı

## 1-Cümlelik Özet
Mevcut Stok Sayım sayfasını EAN/barkod destekli, endüstri standartlarına uygun, lot ve lokasyon bazlı sayım yeteneği kazandırarak yeniden tasarla ve geliştir.

---

## Mevcut Durum Analizi

### Var Olan Özellikler
| Bileşen | Durum |
|---------|-------|
| Sayım başlatma/kapatma | ✓ Mevcut |
| Barkod/Ürün ID girişi | ✓ Var (ancak sadece ID) |
| Upsert mantığı | ✓ Var |
| Varyans raporu | ✓ Var |
| Onay akışı | ✓ Var |
| Durum yönetimi | ✓ Var (oluşturuldu→devam→onaylandı) |

### Kritik Eksiklikler

#### 1. EAN/Barkod Entegrasyonu (Kritik)
- **Problem**: Frontend `parseInt(barkodDegeri)` ile direkt ürün ID'ye çeviriyor
- **Gerçek Dünya Senaryosu**: EAN kodları 8-13 haneli numerik değerlerdir, ürün ID değil
- **Risk**: Hiçbir gerçek barkod tarayıcı bu sistemle çalışamaz

#### 2. Lot Bazlı Sayım (Yüksek)
- **Problem**: Sadece ürün seviyesinde sayım, lot detayı yok
- **Endüstri Standartı**: SKY, SAP gibi sistemler lot bazlı sayım yapar (FIFO/LIFO takibi için kritik)
- **Risk**: Son kullanma tarihi yaklaşan ürünler ayrı sayılamaz

#### 3. Lokasyon/Raf Bazlı Sayım (Yüksek)
- **Problem**: Depo içinde raf/lokasyon bilgisi yok
- **Endüstri Standartı**: "A-01-03 rafında 15 koli X ürünü" şeklinde sayım
- **Risk**: Kaybolan ürünlerin yeri tespit edilemez

#### 4. Birim Yönetimi (Orta)
- **Problem**: Her zaman `sayilan_miktar: 1` gönderiliyor
- **Gerçek Dünya**: Sayıcılar genelde "1 koli değil, 5 koli" görür
- **Risk**: Manuel artırma mantığı kullanıcı deneyimini bozar

#### 5. Çok Kullanıcılı Senkronizasyon (Orta)
- **Problem**: İki kullanıcı aynı anda sayım yaparsa çakışma riski
- **Endüstri Standartı**: WebSocket/SSE ile gerçek zamanlı senkronizasyon

#### 6. Durum Geçiş Hataları (Kritik)
- **Problem**: `BİTTİ` durumuna geçiş hiç kullanılmıyor, doğrudan `ONAYLANDI` yapılıyor
- **Backend Kodu**: @`stok_sayim_use_cases.py:72` - `sayimi_onayla` fonksiyonu
- **Risk**: Sayım tamamlanmadan onaylanabilir

---

## Revize Edilmiş İş Akışı

### Kullanıcı Akışı (Happy Path)
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  1. Sayım Tipi  │───▶│  2. Lokasyon    │───▶│  3. EAN Tara    │
│   Seçimi        │    │   Seçimi        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                              ┌─────────────────────────┘
                              ▼
                     ┌─────────────────┐
                     │  4. Ürün/Lot    │◄────────────────┐
                     │   Doğrulama     │                 │
                     └─────────────────┘                 │
                              │                          │
                              ▼                          │
                     ┌─────────────────┐    ┌───────────┴──┐
                     │  5. Miktar      │───▶│  Başka Ürün? │
                     │   Girişi        │    │   (Evet)     │
                     └─────────────────┘    └──────────────┘
                              │                          │
                              ▼                          │
                     ┌─────────────────┐    ┌───────────┴──┐
                     │  6. Sayımı      │◄───│  Hayır       │
                     │   Bitir         │    │              │
                     └─────────────────┘    └──────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │  7. Varyans     │
                     │   Onay          │
                     └─────────────────┘
```

### Sayım Tipleri (Yeni)
| Tip | Açıklama | Kullanım Senaryosu |
|-----|----------|-------------------|
| `PERIYODIK` | Tüm stok sayımı | Yıl sonu, çeyrek sonu |
| `DONGUSEL` | Belirli kategori/raf döngüsü | Haftalık ABC sayımı |
| `ADHOC` | Anlık/spesifik sayım | Hasar tespiti, şüpheli kayıp |
| `KONTROL` | Sadece kritik stoklar | Min. stok altındakiler |

### Lokasyon Hiyerarşisi (Yeni)
```
Depo → Bölüm → Raf → Göz

Örnek: "ANA-DEPO" → "A-BLOK" → "A-01" → "03"
         ↓           ↓          ↓        ↓
      Depo adı    Bölüm      Raf no   Göz no
```

### EAN İşleme Akışı
```python
# Backend Logic
1. EAN kodu al (8-13 karakter)
2. EAN → Ürün ID çözümlemesi yap
   - Önce EAN alanına bak
   - Sonra barkod alanına bak
   - Bulunamazsa hata dön
3. Ürünün lotlarını getir
4. Sayım kriterine uygun lotları listele
5. Kullanıcı lot seçimi yap (veya otomatik)
6. Sayım kaydı oluştur
```

---

## Uygulama Planı

### Faz 1: Temel EAN Desteği (Zorunlu)
**Süre**: 1-2 gün

#### Backend (@`BackendProje/app/`)
1. **Yeni Endpoint** - `GET /api/urunler/ean/{ean}`
   - EAN ile ürün arama
   - Lot bilgisiyle birlikte döndür
   
2. **DTO Güncelleme** - `@stok_sayim_dto.py`
   - `ean` alanı ekle (alternatif `urun_id`)
   - `lot_id` alanı ekle (opsiyonel)
   - `lokasyon` alanı ekle (opsiyonel)

3. **Use Case Güncelleme** - `@stok_sayim_use_cases.py:122`
   ```python
   # StokSayimKalemKaydetUseCase.execute()
   # Önce EAN ile ürün ara, bulamazsa ID kullan
   if dto.ean:
       urun = self._urun_repo.getir_ean_ile(dto.ean)
   else:
       urun = self._urun_repo.getir_id_ile(dto.urun_id)
   ```

#### Frontend (@`ReactProje/src/pages/StokSayimPage.jsx:50`)
1. **Barkod Input Güncelleme**
   - `type="number"` → `type="text"`
   - EAN validasyonu (8-13 karakter, sadece rakam)
   - EAN → API çağrısı ile ürün çözümleme

2. **Yeni State'ler**
   ```javascript
   const [cozumlenenUrun, setCozumlenenUrun] = useState(null);
   const [mevcutLotlar, setMevcutLotlar] = useState([]);
   ```

### Faz 2: Lot Bazlı Sayım (Yüksek Öncelik)
**Süre**: 2-3 gün

#### Backend
1. **Lot Repository** - Yeni metodlar
   - `getir_urun_lotlari(urun_id, aktif=True)`
   - `getir_lot_bazli_stok(lot_id)`

2. **Sayım Kalemi Entity** - `@stok_sayim.py:26`
   ```python
   @dataclass
   class StokSayimKalemi:
       # ... mevcut alanlar ...
       lot_id: Optional[int] = None  # Yeni
       lokasyon: Optional[str] = None  # Yeni
   ```

3. **Varyans Hesaplama Güncelleme** - `@stok_sayim_use_cases.py:181`
   - Lot bazlı varyans (aynı ürün, farklı lotlar)

#### Frontend
1. **Lot Seçim UI**
   - EAN okutulduktan sonra lot listesi göster
   - Son kullanma tarihi, miktar bilgisi
   - Hızlı seçim için öneri (en eski lot)

2. **Sayım Tablosu Güncelleme**
   - Lot kolonu ekle
   - Lokasyon kolonu ekle

### Faz 3: Lokasyon Yönetimi (Orta Öncelik)
**Süre**: 2-3 gün

#### Backend
1. **Lokasyon Entity** - Yeni
   ```python
   @dataclass
   class Lokasyon:
       id: int
       kod: str  # "A-01-03"
       depo_id: int
       tip: str  # "RAF", "BOLME", "ZEMIN"
   ```

2. **Sayım Başlatma Güncelleme**
   - Opsiyonel lokasyon filtresi
   - Sadece belirli lokasyondaki ürünleri say

#### Frontend
1. **Lokasyon Seçim UI**
   - Ağaç yapısı: Depo → Bölüm → Raf
   - QR kod ile lokasyon tarama

### Faz 4: İleri Seviye Özellikler (Düşük Öncelik)
- Çok kullanıcılı senkronizasyon (WebSocket)
- Barkod yazıcı entegrasyonu
- Mobil tarayıcı optimizasyonu
- Offline-first senkronizasyon

---

## Tespit Edilen Hatalar

### Hata #1: Geçersiz Barkod İşleme
**Konum**: `@ReactProje/src/pages/StokSayimPage.jsx:52`
```javascript
// MEVCUT (HATALI)
const urunId = parseInt(barkodDegeri);

// PROBLEM
// EAN-13: 8691234567890 → 8691234567890 (geçerli)
// Ancak baştaki 0'lar kaybolur: 0123456789012 → 123456789012
```

### Hata #2: Sayım Bitiş Aşaması Eksik
**Konum**: `@stok_sayim_use_cases.py:72`
- `ONAYLANDI` endpoint'i var ama `BITTI` endpoint'i yok
- Kullanıcı sayımı tamamlayıp kontrol edemiyor

### Hata #3: Çakışma Kontrolü Yok
- Aynı ürün iki farklı kullanıcı tarafından sayılırsa son kaydeden kazanır
- Optimistic locking yok

### Hata #4: Miktar Validasyonu Yok
- Negatif miktar gönderilebilir
- Sıfır miktar gönderilebilir (boş kayıt)

---

## Teknik İyileştirmeler

### Backend
| Alan | Mevcut | Öneri |
|------|--------|-------|
| EAN arama | Repository'de var, kullanılmıyor | Use case'e entegre et |
| Transaction | Her kayıtta commit | Batch insert desteği |
| Validasyon | Temel Pydantic | İş kuralı validasyonu |
| Audit trail | Sistem log var | Detaylı audit log |

### Frontend
| Alan | Mevcut | Öneri |
|------|--------|-------|
| Input | Type="number" | Type="text" + validasyon |
| Feedback | Toast mesaj | Ses + vibrasyon (mobil) |
| Hata | Genel hata | Spesifik hata kodları |
| Offline | Yok | LocalStorage buffer |

---

## Başarı Kriterleri

### Fonksiyonel
- [ ] EAN-8, EAN-13, UPC barkodlar desteklenir
- [ ] Barkod tarayıcı ile sayım yapılabilir
- [ ] Lot bazlı sayım desteklenir
- [ ] Lokasyon bazlı sayım desteklenir
- [ ] Manuel miktar girişi yapılabilir

### Performans
- [ ] EAN çözümleme < 500ms
- [ ] Sayım kaydı < 1s
- [ ] Varyans raporu < 2s (1000+ ürün)

### Güvenilirlik
- [ ] Sayım çakışması önlenir
- [ ] Ağ kesintisinde veri kaybı olmaz
- [ ] Audit trail tam ve doğru

---

## Sonraki Adımlar

1. **Faz 1 onayını al** - EAN desteği için kullanıcı onayı
2. **Backend API tasarımı** - Swagger/OpenAPI spec
3. **Frontend mock'ları** - UI prototipi
4. **Test senaryoları** - E2E test planı

---

*Plan oluşturulma tarihi: 2026-04-03*
*Son güncelleme: 2026-04-03*
