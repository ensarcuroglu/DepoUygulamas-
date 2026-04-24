# Zebra El Terminali Barkod Okuma Profesyonelleştirme Planı

Mevcut DepoUygulaması projesindeki barkod okuma akışlarını analiz edip, Zebra fiziksel scanner donanımı ile endüstri standardına uygun, güvenilir entegrasyon önerileri sunan plan.

---

## 1. Mevcut Durum Analizi

### 1.1 Barkod Okuma Mekanizmaları

Uygulamada **3 farklı barkod okuma yolu** var:

| Yöntem | Dosya | Kullanım Yeri |
|--------|-------|---------------|
| **`useBarcodeScanner` hook** | `ReactProje/src/hooks/useBarcodeScanner.jsx` | `UrunlerPage`, `PaletlerPage`, `StokHareketleriPage` |
| **`ZXingBarcodeScanner` component** | `ReactProje/src/components/common/ZXingBarcodeScanner.jsx` | `YerlestirmePage`, `TerminalUretimKabulPage`, `UrunlerPage`, `StokHareketleriPage` |
| **Doğrudan `<input>` + Enter** | Terminal sayfalarındaki input elementleri | `YerlestirmePage`, `TerminalUretimKabulPage` |

### 1.2 `useBarcodeScanner` Hook Detayı

- Window seviyesinde `keydown` dinliyor (capture phase)
- Zebra DataWedge **Keyboard Wedge** modu için tasarlanmış
- `maxGap=150ms` ile hızlı tuş dizisini barkod olarak algılıyor
- Enter tuşu = "okuma bitti" sinyali
- `ignoredInputTypes` ile input/textarea fokuslu iken çift tetikleme önleniyor
- **Terminal sayfalarında kullanılmıyor** — sadece UrunlerPage, PaletlerPage, StokHareketleriPage'te aktif

### 1.3 Terminal Sayfaları Barkod Yönetimi

**YerlestirmePage** (`4 adımlı akış`):
- Adım 2 (Palet): Manuel `<input>` + Enter veya ZXingBarcodeScanner modal
- Adım 3 (Raf): Manuel `<input>` + Enter veya ZXingBarcodeScanner modal
- `useBarcodeScanner` hook **kullanılmıyor**
- Fiziksel scanner tuş vuruşları input'a doğrudan düşüyor, `onKeyDown={Enter}` ile işleniyor

**TerminalUretimKabulPage** (`3 adımlı akış`):
- Adım 1 (Palet): Manuel `<input>` + Enter veya ZXingBarcodeScanner modal
- Adım 2 (Raf): Manuel `<input>` + Enter veya ZXingBarcodeScanner modal
- `useBarcodeScanner` hook **kullanılmıyor**
- `inputRef` ile adım değişiminde `setTimeout(() => inputRef.current?.focus(), 100)` yapılıyor

**GorevListesiPage** ve **TerminalOzetPage**: Barkod okuma yok (sadece navigasyon/istatistik)

### 1.4 StokHareketleriPage (En Gelişmiş Implementasyon)

Bu sayfa en profesyonel barkod yönetimine sahip:
- **`isZebraDevice()`** fonksiyonu ile cihaz algılama (UA: zebra, symbol, tc52, tc21, tc72, mc33)
- **`stripControlChars`** ve **`sanitizePaletNo`** ile DataWedge kontrol karakterleri temizleme
- **`scanFeedback()`** ile sesli (Web Audio API) + dokunsal (Vibration API) geri bildirim
- **`pendingRef`** (Set) ile race condition / duplicate scan koruması
- **`useBarcodeScanner`** hook kullanımı (`ignoredInputTypes: ['input', 'textarea']`)
- **Visibility change** dinleyicisi ile ekran kararma sonrası focus geri kazanımı
- Zebra algılandığında kamera butonu gizleniyor

### 1.5 Backend API Endpoint'leri

`BackendProje/app/api/v1/routers/mobil_terminal.py`:
- `POST /api/terminal/scan/palet` — Palet barkod sorgulama (rate limit: 120/min)
- `POST /api/terminal/scan/raf` — Raf barkod sorgulama (rate limit: 120/min)
- `POST /api/terminal/yerlestir` — Scan-to-verify yerleştirme (rate limit: 60/min)
- `POST /api/terminal/alternatif-raf` — Alternatif raf önerisi
- `POST /api/terminal/log-palet-hata` — Palet hata loglama (KPI)
- `GET /api/terminal/gorevlerim` — Operatör görevleri
- `GET /api/terminal/ozet` — Günlük özet

### 1.6 Backend İdempotency & Concurrency

- **`app/core/idempotency.py`** mevcut: Idempotency-Key tabanlı önbellek (24 saat TTL)
- Use case'lerde `kilitli_mi=True` ile `SELECT ... FOR UPDATE` kullanılıyor (palet, yerlestirme_gorevi)
- Rate limiting aktif (`limiter` middleware)
- **Ancak**: Terminal endpoint'lerinde idempotency_key kontrolü **yok** — sadece stok_islemleri ve bazı diğer endpoint'lerde var

---

## 2. Tespit Edilen Eksikler

### 2.1 Frontend Eksikler

| # | Eksiklik | Açıklama |
|---|----------|----------|
| 1 | **Terminal sayfalarında `useBarcodeScanner` yok** | YerlestirmePage ve TerminalUretimKabulPage, fiziksel scanner için hook kullanmıyor. Input'a düşen tuş vuruşları + Enter ile çalışıyor ama arka plan taraması yok. |
| 2 | **Duplicate scan koruması yok** | Terminal sayfalarında aynı barkodun ardışık okutulmasını engelleyen mekanizma yok. StokHareketleriPage'te `pendingRef` var ama terminal sayfalarında yok. |
| 3 | **Barkod format doğrulama yok** | Palet barkod formatı (ör: `PRD-YYYYMMDD-NNNN`), raf barkod formatı doğrulanmıyor. Hatalı barkod backend'e kadar gidip orada 404 dönüyor. |
| 4 | **Sesli/dokunsal geri bildirim yok** | Terminal sayfalarında `scanFeedback()` fonksiyonu kullanılmıyor. Sadece toast mesajı var. |
| 5 | **Otomatik focus yönetimi zayıf** | `setTimeout(() => inputRef.current?.focus(), 100)` ile yapılıyor ama visibility change, modal kapanma, ekran kararma sonrası focus geri kazanımı yok. |
| 6 | **Zebra cihaz algılama terminal sayfalarında yok** | `isZebraDevice()` sadece StokHareketleriPage'te kullanılıyor. Terminal sayfaları cihaz tipinden habersiz. |
| 7 | **Barkod sanitization terminal sayfalarında yok** | `stripControlChars` ve `sanitizePaletNo` sadece StokHareketleriPage'te lokal tanımlı. Terminal sayfalarında DataWedge kontrol karakterleri temizlenmiyor. |
| 8 | **Hızlı ardışık okutma desteği eksik** | YerlestirmePage'te paletDogrula sonrası RAF adımına geçişte input focus yönetimi tutarsız. |

### 2.2 Backend Eksikler

| # | Eksiklik | Açıklama |
|---|----------|----------|
| 1 | **Terminal endpoint'lerinde idempotency yok** | `/api/terminal/yerlestir` ve `/api/terminal/scan/*` endpoint'lerinde `Idempotency-Key` header kontrolü yok. Aynı barkodun hızlıca 2 kez okutulması duplicate işlem yapabilir. |
| 2 | **Barkod format doğrulama backend'de minimal** | `min_length=1, max_length=100` dışında format kısıtlaması yok. Palet barkod pattern'i, raf barkod pattern'i doğrulanmıyor. |
| 3 | **Scan sonucu önbellek yok** | Aynı palet barkodunu 2 saniye içinde tekrar scan ettiğinizde backend'e tekrar istek gidiyor. |
| 4 | **Concurrent yerleştirme koruması kısmi** | `gorev_repo.getir_id_ile` ile görev çekiliyor ama `FOR UPDATE` kilidi terminal endpoint'inde kullanılmıyor (use case içinde var). |

---

## 3. Zebra Scanner Entegrasyon Seçenekleri

### Seçenek A: DataWedge — Keyboard Wedge (Mevcut Yaklaşım)

**Nasıl çalışır**: DataWedge, fiziksel scanner tetiklendiğinde barkod verisini klavye girişi olarak WebView'a gönderir. Enter tuşu ile sonlandırır.

**Avantajlar**:
- Mevcut kod zaten bu modda çalışıyor
- Ek native kod gerektirmez
- Herhangi bir Android WebView/browser ile uyumlu
- Konfigürasyon basit

**Dezavantajlar**:
- Input focus bağımlı — focus yanlış yerdeyse barkod kaybolur
- Kontrol karakterleri gelebilir (temizleme gerekli)
- DataWedge profil yönetimi cihaz başına manuel
- Scanner butonu özelleştirilemez

**Uygulanabilirlik**: ✅ React WebView'da doğrudan çalışır

### Seçenek B: DataWedge — Intent Output

**Nasıl çalışır**: DataWedge, barkod verisini bir Android Intent olarak yayınlar. Native katman bunu yakalayıp JavaScript'e bridge ile iletir.

**Avantajlar**:
- Input focus bağımsız — arka planda da yakalar
- Barkod formatı, semboloji, uzunluk gibi metadata gelir
- DataWedge profilinden daha fazla kontrol
- Daha güvenilir — klavye girişi yarıklarından etkilenmez

**Dezavantajlar**:
- **React WebView'da doğrudan çalışmaz** — native Android bridge gerekir
- Capacitor/Cordova wrapper veya özel Android katmanı gerekir
- Ek geliştirme maliyeti

**Uygulanabilirlik**: ⚠️ Native wrapper gerekir (Capacitor, veya özel Android WebView)

### Seçenek C: EMDK (Native Android SDK)

**Nasıl çalışır**: Zebra'nın resmi Android SDK'sı. Scanner API'ye doğrudan erişim.

**Avantajlar**:
- Tam kontrol — decoder ayarları, trigger modu, aydınlatma
- En düşük gecikme
- Zebra'nın resmi desteklediği yöntem

**Dezavantajlar**:
- Sadece native Android uygulama — React WebView ile doğrudan uyumsuz
- Büyük geliştirme maliyeti (tam Android uygulaması gerekir)
- Bakım yükü yüksek

**Uygulanabilirlik**: ❌ Mevcut React yapısıyla uyumsuz — tam native geçiş gerekir

### Seçenek D: Hybrid — Capacitor + DataWedge Intent Plugin

**Nasıl çalışır**: Capacitor ile React uygulaması native Android shell'e sarılır. `@capacitor-community/barcode-scanner` veya özel DataWedge Intent listener plugin'i ile Intent'ler yakalanır.

**Avantajlar**:
- Intent Output'un avantajları + React kodu korunur
- Capacitor küçük wrapper — mevcut React kodu minimal değişiklikle çalışır
- Play Store dağıtımı mümkün

**Dezavantajlar**:
- Capacitor kurulumu ve bakımı gerekir
- Debug süreci karmaşıklaşır
- Cihazda APK kurulumu gerekir (PWA değil)

**Uygulanabilirlik**: ✅ Mümkün ama ek native katmanı gerekir

---

## 4. Önerilen En Doğru Yaklaşım

### Aşama 1 (Hemen — Keyboard Wedge Optimizasyonu)

**DataWedge Keyboard Wedge modunu profesyonel seviyede optimize et.** Bu, mevcut yapıyı bozmadan, ek native katmanı olmadan yapılabilecek en etkili iyileştirmedir.

StokHareketleriPage'te zaten var olan ve çalışan pattern'leri terminal sayfalarına taşı:

- `isZebraDevice()` algılama
- `stripControlChars` / `sanitizePaletNo` sanitization
- `scanFeedback()` sesli + dokunsal geri bildirim
- `pendingRef` duplicate scan koruması
- Visibility change + auto-focus yönetimi
- `useBarcodeScanner` hook entegrasyonu

### Aşama 2 (Orta vadeli — Capacitor + Intent Output)

Eğer Aşama 1 yeterli olmazsa veya daha fazla güvenilirlik gerekirse, Capacitor wrapper ile DataWedge Intent Output moduna geçiş. Bu, input focus bağımlılığını tamamen ortadan kaldırır.

---

## 5. Frontend Geliştirme Planı

### 5.1 Paylaşılan Barkod Yardımcı Modülü Oluştur

`ReactProje/src/utils/barcode.js` — StokHareketleriPage'teki lokal fonksiyonları merkezi modüle taşı:

```
- isZebraDevice()
- stripControlChars(value)
- sanitizePaletNo(raw)
- sanitizeBarkod(raw, type)  // 'palet' | 'raf' | generic
- scanFeedback(type)         // 'success' | 'error'
- validateBarkodFormat(code, type) → { valid, error }
```

### 5.2 `useBarcodeScanner` Hook Güçlendirme

`ReactProje/src/hooks/useBarcodeScanner.jsx`:
- `onScan` callback'ine sanitize edilmiş barkod gönder
- Duplicate scan koruması ekle (son N barkodu bellekte tut, aynı barkod X ms içinde tekrar gelirse yoksay)
- Barkod format doğrulama opsiyonu ekle
- `scanFeedback` entegrasyonu (opsiyonel parametre)
- Cihaz algılama sonrası `maxGap` otomatik ayarlama (Zebra: 150ms, PC: 80ms)

### 5.3 Terminal Sayfalarına `useBarcodeScanner` Entegrasyonu

**YerlestirmePage**:
- `useBarcodeScanner` hook ekle (`isEnabled: adim === ADIM.PALET || adim === ADIM.RAF`)
- `ignoredInputTypes: ['input', 'textarea']` ile çift tetikleme önle
- `onScan` callback'inde adıma göre `paletDogrula(code)` veya `yerlestir(code)` çağır
- Auto-focus yönetimi: visibility change + adım geçişi + modal kapanma
- `scanFeedback` ile sesli/dokunsal geri bildirim

**TerminalUretimKabulPage**:
- Aynı pattern — `useBarcodeScanner` hook ekle
- `isEnabled: adim === ADIM.PALET || adim === ADIM.RAF`
- `onScan` → `paletOkut(code)` veya `rafOkut(code)`

### 5.4 Barkod Format Doğrulama

Frontend tarafında regex pattern'leri:

```js
const BARKOD_FORMATLARI = {
  palet: /^PRD-\d{8}-\d{1,4}$/i,   // PRD-YYYYMMDD-NNNN
  raf: /^[A-Z]{2,3}-[A-Z]-\d{2}-\d{2}-\d{2}$/i,  // GNL-A-01-01-01
  lot: /^LOT-\d+$/i,
};
```

Format uyuşmazlığında anında kullanıcıya görsel/seyssel hata geri bildirimi, backend'e gereksiz istek gitmez.

### 5.5 Auto-Focus Yönetim Component'i

`ReactProje/src/components/terminal/ScanFocusManager.jsx`:
- Belirli bir input ref'e sürekli focus garantisi
- Visibility change dinleyicisi
- Modal/sheet kapanma sonrası focus geri kazanımı
- Zebra cihazda ekran kararma sonrası focus restore
- Touch/click olaylarında focus'u input'ta tut

### 5.6 ZXingBarcodeScanner İyileştirmesi

- Zebra cihazda `isZebraDevice()` true ise kamera butonu gizlensin (StokHareketleriPage'teki pattern)
- Kamera fallback olarak kalsın ama terminal sayfalarında ikincil olsun

---

## 6. Backend Geliştirme Planı

### 6.1 Terminal Endpoint'lerine Idempotency Ekle

`/api/terminal/yerlestir` endpoint'ine `Idempotency-Key` header kontrolü ekle:
- Frontend her scan işleminde benzersiz bir key üretip header'a eklesin
- Backend mevcut `idempotency_kontrol` / `idempotency_kaydet` fonksiyonlarını kullansın
- Aynı key ile tekrar gelen isteklerde önceki sonucu dönsün

### 6.2 Barkod Format Dorulama (Pydantic)

`PaletScanRequestDTO` ve `RafScanRequestDTO`'ya regex validasyon ekle:
```python
palet_barkod: str = Field(..., min_length=4, max_length=50, pattern=r'^[A-Z]{2,4}-\d{4,8}-\d{1,4}$')
raf_barkod: str = Field(..., min_length=3, max_length=50, pattern=r'^[A-Z]{2,3}-[A-Z]-\d{2}-\d{2}-\d{2}$')
```

**Not**: Mevcut verideki barkod formatları analiz edilip regex buna göre belirlenmeli. Yukarıdaki örnek varsayımdır.

### 6.3 Scan Sonucu Kısa Süreli Önbellek

Aynı barkodun 5 saniye içinde tekrar scan edilmesinde backend'e istek gitmesin, frontend'de kısa süreli sonuç önbelleği tutulsun. Bu rate limit'i de rahatlatır.

### 6.4 Hata Mesajları İyileştirmesi

Terminal endpoint'lerinden dönen hata mesajlarını operatör dostu hale getir:
- `KayitBulunamadiError` → "Bu barkod sistemde kayıtlı değil. Etiketi kontrol edin."
- `GecersizIslemError` → "Bu palet zaten işlenmiş. Durum: {durum}"
- Kapasite hatası → "Raf dolu! Alternatif raflar yükleniyor..."

---

## 7. Test Planı

### 7.1 Frontend Testleri

| Test | Açıklama |
|------|----------|
| Keyboard Wedge simülasyonu | PC'de hızlı tuş dizisi + Enter ile barkod simülasyonu |
| Duplicate scan engelleme | Aynı barkodu 2 sn içinde tekrar okutma |
| Hatalı format geri bildirimi | Geçersiz barkod formatında anında uyarı |
| Auto-focus geri kazanımı | Modal kapanma, ekran kararma sonrası focus testi |
| Hızlı ardışık okutma | 5 paleti 10 sn içinde okutma |
| Sesli/dokunsal geri bildirim | Başarılı ve hatalı okutma geri bildirimleri |
| Zebra cihaz algılama | isZebraDevice() UA testi |

### 7.2 Backend Testleri

| Test | Açıklama |
|------|----------|
| Idempotency duplicate yerleştirme | Aynı Idempotency-Key ile 2 istek → 1 işlem |
| Concurrent yerleştirme | Aynı göreve 2 farklı raf ile eşzamanlı istek |
| Geçersiz barkod format | 422 response doğrulama |
| Rate limit | 120/min scan limit aşımı |

### 7.3 Fiziksel Cihaz Testleri (Zebra)

| Test | Açıklama |
|------|----------|
| DataWedge Keyboard Wedge + Enter | Fiziksel tetik ile okutma |
| Hızlı ardışık okutma (trigger spam) | 10 barkod 15 sn içinde |
| Ekran kararma + scan | Cihaz ekranı karardığında scan tetikleme |
| Focus kaybı senaryosu | Başka element'e dokunup sonra scan |
| Kontrol karakteri temizleme | DataWedge prefix/suffix karakterleri geliyorsa |

---

## 8. Riskler ve Dikkat Edilecek Noktalar

| Risk | Etki | Önlem |
|------|------|--------|
| **DataWedge profili cihaz başına farklı olabilir** | Enter tuşu gönderilmeyebilir, prefix/suffix eklenebilir | DataWedge profil standardizasyonu + fallback mekanizması |
| **Android WebView GC/rendering gecikmesi** | maxGap=150ms yetersiz kalabilir | Zebra cihazda 200ms'ye çıkarılabilir, test ile doğrula |
| **Focus kaybı kritik** | Keyboard Wedge modunda focus yanlış yerdeyse barkod kaybolur | ScanFocusManager ile sürekli focus garantisi |
| **Barkod format değişkenliği** | Mevcut veride farklı formatlar olabilir | Backend'de regex çok sıkı olmamalı, frontend'de uyarı ama engelleme olmasın |
| **Capacitor geçişi uzun vadeli** | Native wrapper ek geliştirme ve bakım maliyeti | Aşama 1'i tam verimle çalıştır, Capacitor'u sadece gerekirse düşün |
| **Mevcut yapıyı bozma riski** | Terminal sayfaları canlı kullanımda | Her değişikliği feature flag ile koru, eski davranışa dönüş olanağı bırak |

---

## 9. Fazlara Ayrılmış Uygulama Planı

### Faz 1: Paylaşılan Altyapı (2-3 gün)

1. `ReactProje/src/utils/barcode.js` oluştur — `isZebraDevice`, `stripControlChars`, `sanitizeBarkod`, `scanFeedback`, `validateBarkodFormat` fonksiyonlarını StokHareketleriPage'ten taşı
2. `useBarcodeScanner` hook güçlendir — sanitize, duplicate koruma, format doğrulama, feedback entegrasyonu
3. StokHareketleriPage'i refaktör et — lokal fonksiyonları merkezi modülden import et

### Faz 2: Terminal Sayfaları Entegrasyonu (2-3 gün)

4. YerlestirmePage'e `useBarcodeScanner` hook entegre et + auto-focus yönetimi
5. TerminalUretimKabulPage'e `useBarcodeScanner` hook entegre et + auto-focus yönetimi
6. Her iki sayfaya `scanFeedback`, `sanitizeBarkod`, duplicate scan koruması ekle
7. Zebra cihaz algılama ile kamera butonu koşullu gösterimi

### Faz 3: Backend Güçlendirme (1-2 gün)

8. `/api/terminal/yerlestir` endpoint'ine idempotency ekle
9. Barkod DTO'lara format validasyon ekle (sıkı olmayan, uyarı seviyesinde)
10. Hata mesajlarını operatör dostu hale getir

### Faz 4: Fiziksel Cihaz Doğrulama (1 gün)

11. Zebra cihazda DataWedge profili kontrol et ve standardize et
12. Fiziksel test senaryolarını çalıştır
13. maxGap, focus timing gibi parametreleri cihazda kalibre et

### Faz 5 (Opsiyonel): Capacitor + Intent Output

14. Capacitor projesi kur
15. DataWedge Intent listener plugin'i geliştir
16. React uygulamasını Capacitor içine sar
17. Intent Output modunu test et

---

## 10. Fiziksel Cihaz Kontrol Listesi

**Zebra cihazda doğrulanması gerekenler:**

- [ ] Cihaz modeli (ör: TC21, TC52, MC3300) ve Android sürümü kaydedildi
- [ ] DataWedge uygulaması yüklü ve aktif
- [ ] DataWedge profili: "Keyboard Wedge" modu aktif
- [ ] DataWedge profili: "Send ENTER key" ayarı açık
- [ ] DataWedge profili: Keystroke output → Inter-character delay (varsayılan: 0ms)
- [ ] DataWedge profili: Prefix/Suffix karakterleri tanımlı mı? (genelde boş olmalı)
- [ ] DataWedge profili: Barcode türleri (CODE_128, EAN_13, CODE_39, QR vs.) aktif
- [ ] Uygulama WebView'ında input focus iken fiziksel tetik çalışıyor mu?
- [ ] Hızlı ardışık okutmada karakter kaybı oluyor mu?
- [ ] Ekran kararma (screen timeout) sonrası scan tetik çalışıyor mu?
- [ ] WebView JavaScript console'da barkod karakterleri doğru görünüyor mu?
- [ ] `navigator.vibrate` ve Web Audio API çalışıyor mu?
- [ ] Cihazın User-Agent string'i `isZebraDevice()` tarafından algılanıyor mu?

**DataWedge Profil Export/Import**: Zebra cihazlarda profil `.db` dosyası olarak export/import edilebilir. Bir cihazda profili oluşturup diğer cihazlara dağıtmak en verimli yöntemdir.

---

## Mevcut Net Bilgiler

Cihaz: Zebra TC52AX
Android: 11
Uygulama: Chrome browser üzerinden React web app
Barkod türleri: Code 128 + QR
Palet formatı: PRD-20260424-001
Raf formatı: GNL-A-01-01-01
İstenen davranış: Scan sonrası ENTER gönderilsin
Önerilen yöntem: DataWedge Keyboard Wedge / Keystroke Output
