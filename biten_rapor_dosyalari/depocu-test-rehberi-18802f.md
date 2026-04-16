# Depocu Gerçek Hayat Test Rehberi — "Tır Gelişi" Senaryosu

Bu doküman, bir depocunun sistem üzerinden TIR gelişinden itibaren yapacağı tüm adımları adım adım anlatır.

---

## Senaryo Özeti

**Başlangıç**: Tır depoya geldi, ürünler boşaltılacak  
**Bitiş**: Ürünler sisteme kaydedildi, paletler raflara yerleştirildi

**Rol**: `depocu`  
**Ana Sayfalar**: `/stok-hareketleri`, `/mal-kabul-irsaliyeleri`, `/terminal/gorevler`

---

## Aşama 1: Sisteme Giriş ve Genel Bakış

### 1.1 Giriş Yap
- **URL**: `http://localhost:5173/login` (veya deploy edilmiş URL)
- **Kullanıcı**: `depocu` rolünde bir hesap
- **Şifre**: sistemde tanımlı şifre

### 1.2 Ana Sayfa — Stok Hareketleri
Giriş yaptıktan sonra depocu otomatik `/stok-hareketleri` sayfasına yönlendirilir.

**Ne görürsün?**
- Üst menüde: Barkod Okuyucu, Manuel Giriş/Çıkış butonları
- Tablo: Son stok hareketleri listesi
- Sayfalama ve filtreleme seçenekleri

**Test Kontrolü:**
- [ ] Menüde "Stok Hareketleri" aktif mi?
- [ ] Son hareketler tablosu yükleniyor mu?
- [ ] Filtreler çalışıyor mu?

---

## Aşama 2: Mal Kabul — İrsaliye Oluşturma

Tır geldi, irsaliye var. İrsaliye sistemde yoksa **yeni irsaliye oluşturulmalı**.

### 2.1 Mal Kabul İrsaliyeleri Sayfasına Git
- **Navigasyon**: Sol menü → "Mal Kabul İrsaliyeleri" veya doğrudan `/mal-kabul-irsaliyeleri`

**Ne görürsün?**
- İrsaliye listesi (durumlar: Taslak, Bekliyor, İşlemde, Tamamlandı)
- "Yeni İrsaliye" butonu

### 2.2 Yeni İrsaliye Oluştur

**Adımlar:**
1. "Yeni İrsaliye" butonuna tıkla
2. Formu doldur:
   - **Tedarikçi**: Dropdown'dan seç (örn: "ABC Tedarikçi")
   - **Depo**: Hangi depoya geldi (örn: "Ana Depo")
   - **Fiili Tarih**: Tır'ın geldiği tarih (bugün)
   - **Açıklama**: Opsiyonel not
3. "Kaydet" butonu

**Beklenen:** İrsaliye oluşturulur, otomatik numara atanır (`MKI-2024-00001` formatında)

**Test Kontrolü:**
- [ ] Form doğrulama çalışıyor mu? (boş alan hatası veriyor mu?)
- [ ] Otomatik irsaliye numarası atandı mı?
- [ ] İrsaliye listesinde "Taslak" durumunda görünüyor mu?

### 2.3 İrsaliye Kalemleri Ekle (Palet Bilgileri)

Tır'daki her ürün/palet için kalem eklenir.

**Adımlar:**
1. İrsaliye listesinden yeni oluşturulan irsaliyeye tıkla
2. "Kalem Ekle" butonu
3. Formu doldur:
   - **Ürün**: Dropdown'dan seç (ürünler önceden tanımlı olmalı)
   - **LOT/Parti**: Ürünün parti numarası
   - **Miktar**: Kaç adet/adetlik
   - **Palet No**: Fiziksel palet numarası (opsiyonel, sistem üretebilir)
   - **SKT**: Son kullanma tarihi (eğer varsa)
4. "Ekle" butonu

**Kaç kalem?** Tır'da 3-5 farklı ürün varsa, 3-5 kalem ekle.

**Test Kontrolü:**
- [ ] Ürün seçimi çalışıyor mu?
- [ ] Miktar sadece sayı kabul ediyor mu?
- [ ] Palet no otomatik üretebiliyor mu?
- [ ] Kalemler listeleniyor mu?

---

## Aşama 3: İrsaliyeyi Onayla ve Yerleştirme Görevi Oluştur

### 3.1 İrsaliyeyi Onayla

Tüm kalemler eklendikten sonra:

**Adımlar:**
1. İrsaliye detay sayfasında "Onayla" butonuna tıkla
2. Sistem otomatik olarak her kalem için **Yerleştirme Görevi** oluşturur

**Ne olur?**
- İrsaliye durumu: "İşlemde" → "Tamamlandı"
- Her kalem için otomatik yerleştirme görevi oluşur
- Önerilen raf bilgisi sistem tarafından atanır

**Test Kontrolü:**
- [ ] Onaylama başarılı mı?
- [ ] İrsaliye durumu değişti mi?
- [ ] Hata mesajı var mı?

---

## Aşama 4: Mobil Terminal — Yerleştirme Görevlerini Tamamla

Bu aşama **saha çalışanı (depocu)** tarafından mobil cihaz veya terminal üzerinden yapılır.

### 4.1 Terminal Ekranına Git
- **URL**: `/terminal/gorevler`
- **Görünüm**: Koyu tema, saha için optimize edilmiş UI

**Ne görürsün?**
- Bekleyen yerleştirme görevleri listesi
- Her görevde: Palet No, Ürün Adı, Önerilen Raf, Öncelik

### 4.2 Görev Ata (Opsiyonel)

Eğer süpervizör atama yapmamışsa, depocu kendine görev alabilir:

**Adımlar:**
1. Görev listesinden bir göreve tıkla
2. "Üzerime Al" veya "Başlat" butonu

### 4.3 Yerleştirme İşlemini Yap

**Adımlar:**
1. Terminalde görevi seç → `/terminal/yerlestirme?gorev_id=XXX`
2. Barkod okuyucu ile **Palet No** oku (veya manuel gir)
3. Sistem önerilen rafı gösterir (örn: "A-01-03")
4. **Fiziksel kontrol**: Paleti o rafa kaldır (veya farklı bir raf seç)
5. Eğer farklı raf kullanıldıysa: "Farklı Raf" seçeneği işaretle
6. **Gerçekleşen Raf** seçimi yap
7. "Tamamla" butonu

**Test Kontrolü:**
- [ ] Barkod okuma çalışıyor mu? (eğer kamera varsa)
- [ ] Palet bilgisi doğru geliyor mu?
- [ ] Önerilen raf görünüyor mu?
- [ ] Farklı raf seçimi aktif mi?
- [ ] Tamamla butonu görevi bitiriyor mu?

---

## Aşama 5: Stok Sorgulama ve Doğrulama

### 5.1 Palet Sorgula
- **Sayfa**: `/stok-hareketleri`
- **Özellik**: "Barkod Oku" veya "Palet Sorgula"

**Adımlar:**
1. Yerleştirilen paletin barkodunu oku
2. Sistem palet bilgisini gösterir:
   - Ürün adı
   - Miktar
   - Bulunduğu raf
   - Son hareket tarihi

**Test Kontrolü:**
- [ ] Palet sorgulama doğru sonuç dönüyor mu?
- [ ] Raf bilgisi güncel mi?

---

## Aşama 6: Stok Çıkış (Opsiyonel — Sevkiyat)

Eğer aynı gün sevkiyat da varsa:

### 6.1 Sevkiyat Planlama
- **Sayfa**: `/sevkiyatlar` veya `/sevkiyat-planlama`

**Adımlar:**
1. Yeni sevkiyat oluştur (eğer yoksa)
2. Sevkiyata ürün/palet ekle
3. Sevkiyatı onayla

### 6.2 Stok Çıkış Yap
- **Sayfa**: `/stok-hareketleri`
- **İşlem**: "Palet Çıkış"

**Adımlar:**
1. Barkod okuyucu ile palet no oku
2. Çıkış tipi seç (Sevkiyat, İade, vb.)
3. Onayla

---

## Hata ve İstisna Senaryoları (Mutlaka Test Edilmeli)

### E1: Palet Zaten Sistemde Var
- **Senaryo**: Aynı palet no ile tekrar giriş yapılmaya çalışılırsa
- **Beklenen**: Uyarı: "Bu palet zaten mevcut" veya idempotent davranış (mevcut kaydı döndür)

### E2: Yanlış Raf Yerleştirme
- **Senaryo**: Önerilen raf yerine farklı bir raf kullanımı
- **Beklenen**: Override seçeneği, süpervizör onayı gerekebilir

### E3: SKT Geçmiş Ürün
- **Senaryo**: Son kullanma tarihi geçmiş ürün girişi
- **Beklenen**: Uyarı veya engelleme

### E4: Kapasite Dolu Raf
- **Senaryo**: Önerilen raf doluysa
- **Beklenen**: Alternatif raf önerisi veya kapasite aşımı uyarısı

---

## Raporlama ve Kontrol

### Admin/Lojistik Dashboard
- **Sayfa**: `/dashboard` (admin) veya `/inbound-dashboard` (lojistik)
- **Ne kontrol edilir?**
  - Bugünkü mal kabul sayısı
  - Bekleyen yerleştirme görevleri
  - Tamamlanan işlem istatistikleri

---

## Test Sonuçlarını Raporlama

Her adımı test ettikten sonra aşağıdaki formatta geri bildirim verin:

```
AŞAMA: [1.1, 2.2, vb.]
DURUM: [✅ Başarılı / ❌ Hata / ⚠️ Sorun]
AÇIKLAMA: [Ne yaptınız, ne oldu]
EKRAN GÖRÜNTÜSÜ: [varsa]
HATA MESAJI: [varsa]
ÖNERİ: [İyileştirme öneriniz]
```

---

## Sık Kullanılan URL'ler (Bookmark için)

| Sayfa | URL | Rol |
|-------|-----|-----|
| Login | `/login` | Herkes |
| Stok Hareketleri | `/stok-hareketleri` | Herkes |
| Mal Kabul | `/mal-kabul-irsaliyeleri` | admin, depocu, lojistik |
| Terminal Görevler | `/terminal/gorevler` | admin, depocu, lojistik |
| Yerleştirme | `/terminal/yerlestirme` | admin, depocu, lojistik |
| Sevkiyatlar | `/sevkiyatlar` | Herkes |
| Dashboard | `/dashboard` | admin |
| Inbound Dashboard | `/inbound-dashboard` | admin, lojistik |

---

## Sonraki Test Senaryoları

1. **Gece Vardiyası**: Aynı süreç gece vardiyasında test edilebilir
2. **Çoklu Tır**: Aynı anda 2-3 farklı TIR için paralel işlem
3. **Acil Sevkiyat**: Mal kabul yapmadan doğrudan çapraz sevkiyat (cross-docking)
4. **Sayım**: Stok sayımı süreci

---

*Rehber hazır. Testlere başlayabilirsiniz. Her adımda karşılaştığınız sorunları ve önerilerinizi paylaşın.*
