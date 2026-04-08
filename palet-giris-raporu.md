# Palet Giriş ve Yerleştirme İş Akışı Analiz Raporu

## 1) Kapsam ve İnceleme Yöntemi
- Kapsam: `Mal Kabul İrsaliyesi` oluşturma/onay, `Stok İşlemleri > Palet Giriş`, `Yerleştirme Görevleri` ve `Mobil Terminal` akışı.
- İncelenen katmanlar: Frontend (React), API router, use-case, domain service, repository.
- Ek doğrulama: ilgili backend testleri çalıştırıldı ve geçti (`41 passed`).
  - Çalıştırılan testler: `tests/api/routers/test_stok_islemleri_api.py`, `tests/api/routers/test_yerlestirme_gorevleri_api.py`, `tests/integration/test_putaway_uctan_uce.py`

## 2) Mevcut As-Is Akış (Özet)
1. Kullanıcı `Mal Kabul İrsaliyesi` oluşturuyor (`Taslak`).
2. UI’den durum manuel `Onaylandi` yapılıyor ([`ReactProje/src/pages/MalKabulIrsaliyeleriPage.jsx:412`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/MalKabulIrsaliyeleriPage.jsx:412)).
3. `Stok İşlemleri` ekranında `Onaylandi` irsaliyeler listeleniyor ([`ReactProje/src/pages/StokHareketleriPage.jsx:169`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/StokHareketleriPage.jsx:169)).
4. Operatör paletleri tarayıp `toplu-giris` çağırıyor; referans irsaliye no ayrı parametre olarak gönderiliyor ([`ReactProje/src/pages/StokHareketleriPage.jsx:321`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/StokHareketleriPage.jsx:321), [`ReactProje/src/pages/StokHareketleriPage.jsx:322`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/StokHareketleriPage.jsx:322)).
5. Ayrı bir putaway/terminal akışı da mevcut (görev al, palet okut, raf okut, yerleştir).

## 3) Kritik Bulgular (P0)

### K1) Onay akışı ile putaway otomasyonu kopuk (mimari kırık)
- Sistemde `IrsaliyeOnaylaVeGorevOlusturUseCase` var ([`BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:283`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:283)) ve DI’da tanımlı ([`BackendProje/app/infrastructure/di/modules/siparis_lojistik_di.py:230`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/infrastructure/di/modules/siparis_lojistik_di.py:230)).
- Ancak router onay için bunu kullanmıyor; genel `PUT` ile status değiştiriyor ([`BackendProje/app/api/v1/routers/mal_kabul_irsaliyeleri.py:71`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/api/v1/routers/mal_kabul_irsaliyeleri.py:71), [`BackendProje/app/api/v1/routers/mal_kabul_irsaliyeleri.py:76`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/api/v1/routers/mal_kabul_irsaliyeleri.py:76), [`BackendProje/app/infrastructure/di/modules/siparis_lojistik_di.py:215`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/infrastructure/di/modules/siparis_lojistik_di.py:215)).
- **Ayrı bir onay endpoint’i (`POST /{id}/onayla`) mevcut değil** — tüm durum geçişleri genel güncelleme endpoint’i üzerinden yapılıyor.
- Frontend’de onay butonu doğrudan `updateMalKabulIrsaliye(id, { durum: ‘Onaylandi’ })` çağırıyor ([`ReactProje/src/pages/MalKabulIrsaliyeleriPage.jsx:177`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/MalKabulIrsaliyeleriPage.jsx:177)), yani `MalKabulIrsaliyeGuncelleUseCase`’e düşüyor.
- Sonuç: “Onay” ile otomatik palet+görev üretimi tetiklenmiyor; eski/yeni akış aynı anda yaşıyor.

### K2) Frontend/Backend endpoint uyuşmazlığı (görev çekme kırık)
- Backend: `POST /yerlestirme-gorevleri/siradaki-al` ([`BackendProje/app/api/v1/routers/yerlestirme_gorevleri.py:103`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/api/v1/routers/yerlestirme_gorevleri.py:103)).
- Frontend: `POST /yerlestirme-gorevleri/sonraki-gorevi-al` ([`ReactProje/src/services/api.js:380`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/services/api.js:380)).
- Sonuç: Terminalde “Sıradaki görevi al” çağrısı üretimde 404/başarısızlık riski taşır.

### K3) Depo seçimi görev atamasını etkilemiyor (yanlış depodan görev alma riski)
- Terminal depo seçiyor ve sadece yerleştirirken `depo_id` gönderiyor ([`ReactProje/src/pages/terminal/YerlestirmePage.jsx:130`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/terminal/YerlestirmePage.jsx:130)).
- Görev çekme çağrısı depo parametresiz ([`ReactProje/src/pages/terminal/YerlestirmePage.jsx:76`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/terminal/YerlestirmePage.jsx:76)).
- Backend görev çekme sadece `Bekliyor` filtresi ile çalışıyor ([`BackendProje/app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py:76`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py:76)).
- Görev entity’sinde `depo_id` yok ([`BackendProje/app/core/entities/yerlestirme_gorevi.py:50`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/core/entities/yerlestirme_gorevi.py:50)).
- Sonuç: Operatör yanlış depo görevini çekebilir; saha operasyonu bozulur.

### K4) “Tek transaction” iddiası bozuluyor (atomiklik riski)
- Use-case tek transaction hedefliyor ([`BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:298`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:298), [`BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:408`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:408)).
- Ama görev repo `olustur` içinde doğrudan commit ediyor ([`BackendProje/app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py:44`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py:44), [`BackendProje/app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py:48`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py:48)).
- Sonuç: hata durumunda kısmi kayıt kalabilir (palet/hareket/görev senkronu bozulabilir).

### K5) Seçilen mal kabul belgesi ile taranan paletler arasında bağ yok
- UI seçilen irsaliye no’yu payload’a ekliyor ([`ReactProje/src/pages/StokHareketleriPage.jsx:322`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/StokHareketleriPage.jsx:322)).
- Ancak taranan paletler tek tek sadece `palet_sorgula` ile doğrulanıyor ([`ReactProje/src/pages/StokHareketleriPage.jsx:251`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/StokHareketleriPage.jsx:251)); belge-paleti eşleştiren bir kontrol zinciri yok.
- Sonuç: Operatör farklı irsaliyeye ait paleti yanlış belge altında girişleyebilir (izlenebilirlik riski).

## 4) Yüksek Öncelikli Bulgular (P1)

### Y1) UI “Raf opsiyonel”, backend “raf zorunlu”
- Formda raf alanı opsiyonel gösteriliyor ([`ReactProje/src/pages/MalKabulIrsaliyeleriPage.jsx:596`](/d:/Ensar Dosya/DepoUygulaması/ReactProje/src/pages/MalKabulIrsaliyeleriPage.jsx:596)).
- Palet giriş service raf_id zorunlu diyor ([`BackendProje/app/core/services/palet_giris_service.py:77`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/core/services/palet_giris_service.py:77)).
- Sonuç: kullanıcı doğal akışta bloklanıyor.

### Y2) STAGING tespiti kod desenine hard-coded
- STAGING bulma ve sevkiyat engeli raf kod desenine bağlı ([`BackendProje/app/infrastructure/persistence/repositories/sa_raf_repository.py:73`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/infrastructure/persistence/repositories/sa_raf_repository.py:73), [`BackendProje/app/core/services/palet_cikis_service.py:200`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/core/services/palet_cikis_service.py:200)).
- Sonuç: kod standardı değişirse kritik kurallar sessizce bozulabilir.

### Y3) Onay+görev use-case semantiği riskli
- Use-case kalemleri `giris_yapildi` yapıp sonra irsaliyeyi `onayla` ediyor ([`BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:390`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:390), [`BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:392`](/d:/Ensar Dosya/DepoUygulaması/BackendProje/app/application/use_cases/mal_kabul_irsaliye_use_cases.py:392)).
- **Not:** K4 ile doğrudan ilişkili — `gorev_repo.olustur()` use-case transaction'ı dışında commit ediyor, bu durumda `giris_yapildi` ve `onayla` henüz commit edilmemiş iken görevler DB'ye yazılmış oluyor.
- Sonuç: fiziksel yerleştirme bitmeden “giriş yapıldı” semantiği oluşuyor; süreç raporlaması yanıltıcı olabilir.

### Y4) Atanmış görevlerde timeout/reclaim mekanizması yok
- Görev `Atandi` olduktan sonra sadece kullanıcı “bırak” aksiyonuyla geri dönebiliyor.
- Sonuç: operatör cihazı kapanırsa görev havuzda kilitli kalma riski.

## 5) Orta Öncelikli Bulgular (P2)

### O1) Terminalde palet doğrulama UX’i zayıf
- Palet adımında güçlü ön doğrulama yok; hata daha geç adımda çıkıyor.

### O2) Aynı işin iki ana yolu var (legacy palet-giriş vs putaway)
- Operasyonel eğitim ve bakım maliyeti yükseliyor; kullanıcıda “doğru yol hangisi?” belirsizliği yaratıyor.

### O3) UTC naive datetime kullanım uyarıları
- Testlerde yoğun `datetime.utcnow()` deprecation warning var; kısa vadede işlevsel risk düşük, uzun vadede teknik borç.

## 6) Endüstri Standardı Hedef Akış (To-Be)
1. **Taslak İrsaliye** oluşturulur (kalem + lot + planlanan depo).
2. **Onay işlemi tek endpoint** ile yapılır: `POST /mal-kabul-irsaliyeleri/{id}/onayla`.
3. Onayda atomik olarak:
   - Paletler oluşturulur,
   - STAGING’e alınır,
   - Yerleştirme görevleri üretilir,
   - Durum `Onaylandi` olur.
4. Operatör **depo bazlı FIFO** görev çeker.
5. Scan-to-verify ile yerleştirme yapar (zon + kapasite kontrol).
6. Tüm görevler tamamlanınca irsaliye otomatik `Tamamlandi` olur.
7. STAGING’te kalan paletler raporlanır ve sevkiyat blokajı devam eder.

## 7) Önerilen Aksiyon Planı

### P0 (hemen)
1. `siradaki-al` endpoint mismatch fix (frontend path düzelt).
2. Onay use-case transaction atomikliğini düzelt (`gorev_repo.olustur` auto_commit kontrollü olmalı).
3. Mal kabul onayını `IrsaliyeOnaylaVeGorevOlusturUseCase` ile entegre et; ayrı onay endpoint’i aç.
4. Görev çekmeyi depo bazlı yap — `YerlestirmeGorevi` entity’sine `depo_id` alanı ekle (denormalize; JOIN yerine doğrudan filtreleme ile terminal performansı korunur).
5. Belge-paleti eşleştirmesini backend’de zorunlu kıl (seçilen irsaliye dışı palet reddi).

### P1
1. Raf zorunluluğu: backend’de otomatik STAGING (Mal Kabul) ataması yapılır; UI’da raf opsiyonel kalır. Onay sırasında raf atanmamış kalemler STAGING’e düşer → Dock-to-Stock akışı korunur, sevkiyat blokajı devam eder.
2. STAGING’i kod paterninden değil explicit bayrak/zon tipi ile yönet.
3. Atanmış görevler için 60 dk timeout + auto-release mekanizması ekle. Timeout süresi sistem ayarlarında konfigüre edilebilir (`PUTAWAY_TIMEOUT`).

### P2
1. Legacy `stok-islemleri/palet-giris` akışını kademeli kapat veya yalnız “istisna operasyon”a indir.
2. Terminalde adım-2 palet doğrulamasını güçlendir (görev paleti ile erken eşleşme).
3. UTC aware datetime standardizasyonu.

## 8) Sonuç
- Mevcut yapı güçlü parçalar içeriyor (test kapsamı iyi, putaway domain modeli iyi), ancak süreç uçtan uca **tek bir kaynak akış** olarak kapanmıyor.
- En kritik sorunlar: **onay entegrasyonu eksikliği**, **endpoint uyuşmazlığı**, **depo filtresiz görev atama**, **atomiklik kırığı**.
- Bu 4 başlık düzeltilmeden “kusursuz, endüstri standardı” operasyon seviyesine çıkmak zor.

---

## 9) Uygulama Planı

### Faz P0 — Kritik Düzeltmeler (hemen)

**Adım 1: Endpoint mismatch fix (K2)** ✅ TAMAMLANDI
- **Dosya:** `ReactProje/src/services/api.js:380`
- **Değişiklik:** `sonraki-gorevi-al` → `siradaki-al`
- **Etki:** Tek satır frontend fix. Hiçbir backend değişikliği gerekmez.

**Adım 2: gorev_repo atomiklik fix (K4)** ✅ TAMAMLANDI
- **Dosya:** `BackendProje/app/infrastructure/persistence/repositories/sa_yerlestirme_gorevi_repository.py`
- **Değişiklik:** `olustur()` metoduna `auto_commit=False` parametresi ekle (palet/hareket repo'lar gibi). Varsayılan `True` kalarak geriye uyumluluğu koru.
- **Interface:** `IYerlestirmeGoreviRepository.olustur()` imzası da güncellenmeli.
- **Etki:** Use-case'deki `self._db.commit()` / `rollback()` artık tek transaction olarak çalışır.

**Adım 3: Onay endpoint entegrasyonu (K1)**
- **Backend:**
  - `mal_kabul_irsaliyeleri.py` routerine `POST /{id}/onayla` endpoint ekle.
  - Bu endpoint `IrsaliyeOnaylaVeGorevOlusturUseCase`'i kullanır.
  - DI container'dan `get_irsaliye_onayla_ve_gorev_olustur_uc` inject edilir (zaten kayıtlı).
- **Frontend:**
  - `api.js`'e `onaylaMalKabulIrsaliye(id)` fonksiyonu ekle → `POST /mal-kabul-irsaliyeleri/{id}/onayla`.
  - `MalKabulIrsaliyeleriPage.jsx:412`'deki `durumDegistir(irs.id, 'Onaylandi')` çağrısını `onaylaMalKabulIrsaliye(irs.id)` ile değiştir.
- **Etki:** Onay tetiklendiğinde otomatik palet + stok hareketi + yerleştirme görevi oluşturulur.

**Adım 4: Depo bazlı görev çekme (K3)**
- **Karar:** `YerlestirmeGorevi` entity'sine `depo_id` alanı doğrudan eklenir (denormalize). JOIN yerine doğrudan filtreleme ile terminal performansı korunur; ileride depo bazlı yetkilendirmeyi de kolaylaştırır.
- **Backend:**
  - `YerlestirmeGorevi` entity'sine `depo_id: int` alanı ekle.
  - `YerlestirmeGoreviORM` modeline `depo_id` kolonu + ForeignKey ekle.
  - `sa_yerlestirme_gorevi_repository.py` `sonraki_gorevi_kilitle()` metoduna `depo_id` filtresi ekle.
  - `/siradaki-al` endpoint'ine `depo_id` query parametresi ekle.
  - `IrsaliyeOnaylaVeGorevOlusturUseCase`'de görev oluştururken `depo_id=irsaliye.depo_id` set et.
- **Frontend:**
  - `YerlestirmePage.jsx:76` `siradakiGorevisiniAl()` çağrısına `depo_id` parametresi gönder.
  - `api.js`'deki `siradakiGorevisiniAl` fonksiyonunu `depo_id` parametresi kabul edecek şekilde güncelle.
- **Etki:** Operatör sadece kendi deposundaki görevleri çeker.

**Adım 5: Belge-palet eşleştirme zorunluluğu (K5)**
- **Backend:**
  - `stok_islemleri` toplu giriş use-case/service'inde `irsaliye_no` parametresi geldiğinde, taranan paletlerin o irsaliye kalemlerinde tanımlı olup olmadığını kontrol et.
  - Eşleşmeyen paletleri reddet (hata dön).
- **Frontend:**
  - Hata durumunu tarama listesinde göster (mevcut error handling yeterli).
- **Etki:** Farklı irsaliyeye ait palet yanlış belge altında girişlenemez.

### Faz P1 — Yüksek Öncelikli İyileştirmeler

**Adım 6: UI/Backend raf zorunluluğu tekleştirme (Y1)**
- **Karar:** Backend'de otomatik STAGING ataması yapılır (Dock-to-Stock akışı). UI'da raf opsiyonel kalır.
- **Backend:**
  - `palet_giris_service.py:75-78`'deki `raf_id` zorunluluk kontrolünü kaldır.
  - `raf_id` yoksa otomatik olarak STAGING rafı ata (mevcut `IrsaliyeOnaylaVeGorevOlusturUseCase` zaten bunu yapıyor).
  - Sevkiyat blokajı korunur: STAGING'deki paletler sevk edilemez.
- **Frontend:**
  - `MalKabulIrsaliyeleriPage.jsx:596` — raf alanı opsiyonel olarak kalır, değişiklik gerekmez.
- **Etki:** Kullanıcı doğal akışta bloklanmaz; yerleştirme tamamlanana kadar sevkiyat blokajı devam eder.

**Adım 7: STAGING tespitini explicit bayrak ile yönet (Y2)**
- `Raf` entity/modeline `is_staging: bool` alanı ekle.
- `getir_staging_raf()` ve `_is_staging_raf()` metotlarını bu bayrağa göre çalıştır.
- Migration: mevcut `%-X-00-00-00` kodlu rafları `is_staging=True` olarak işaretle.

**Adım 8: Timeout/auto-release mekanizması (Y4)**
- **Karar:** 60 dk varsayılan timeout, `PUTAWAY_TIMEOUT` ortam değişkeni ile konfigüre edilebilir.
- `YerlestirmeGorevi` entity'sine `atanma_tarihi` alanı ekle (mevcut `baslama_tarihi`'nden farklı — `baslama_tarihi` paleti fiziksel olarak aldığı an).
- Periyodik bir iş (cron/scheduled task veya API endpoint tetiklemeli) ile `Atandi` durumundaki ve `PUTAWAY_TIMEOUT` süresini aşmış görevleri `Bekliyor`'a çevir, `atanan_kullanici_id`'yi temizle.
- Admin dashboard'da “kilitli görevler” uyarısı göster.
- **Etki:** Operatör cihazı kapandığında veya mola verdiğinde görev havuzda kilitli kalmaz, başka operatöre devredilebilir.

### Faz P2 — Orta Öncelikli İyileştirmeler

**Adım 9: Terminal palet doğrulama güçlendirme (O1)**
- `YerlestirmePage.jsx` `paletDogrula()` fonksiyonunda taranan barkodun görevin palet numarası ile eşleştiğini kontrol et.
- Eşleşmezse kullanıcıya uyarı göster, devam etmeyi engelle.

**Adım 10: Legacy palet-giriş akışını kademeli kapat (O2)**
- `StokHareketleriPage.jsx`'teki palet giriş akışını “İstisna Operasyon” olarak işaretle.
- UI'da bilgilendirme mesajı ekle: “Normal giriş için Mal Kabul İrsaliyesi kullanınız.”
- Uzun vadede bu akışı tamamen kaldırmayı değerlendir.

**Adım 11: UTC aware datetime standardizasyonu (O3)**
- `datetime.utcnow()` → `datetime.now(timezone.utc)` migration'ı yap.
- Entity ve test dosyalarında toplu değiştirme.

### Bağımlılık Grafiği

```
Adım 1 (K2) ──────────────── bağımsız, hemen yapılabilir
Adım 2 (K4) ──────────────── bağımsız, hemen yapılabilir
Adım 3 (K1) ── Adım 2'ye bağlı (atomiklik fix'i önce)
Adım 4 (K3) ──────────────── bağımsız
Adım 5 (K5) ── Adım 3'e bağlı (onay akışı netleşmeli)
Adım 6 (Y1) ── Adım 3'e bağlı (onay entegrasyonu sonrası netleşir)
Adım 7 (Y2) ──────────────── bağımsız
Adım 8 (Y4) ──────────────── bağımsız
Adım 9 (O1) ──────────────── bağımsız
Adım 10 (O2) ─ Adım 3'e bağlı (ana akış yerleştikten sonra)
Adım 11 (O3) ─────────────── bağımsız
```

### Önerilen Uygulama Sırası

| Sıra | Adım | Bulgu | Tahmini Karmaşıklık |
|------|------|-------|---------------------|
| 1 | Adım 1 | K2 | Düşük (1 satır) |
| 2 | Adım 2 | K4 | Düşük (repo + interface) |
| 3 | Adım 4 | K3 | Orta (entity + repo + API + FE) |
| 4 | Adım 3 | K1 | Orta (router + FE entegrasyonu) |
| 5 | Adım 5 | K5 | Orta (backend validasyon) |
| 6 | Adım 6 | Y1 | Düşük (Adım 3 ile çözülür) |
| 7 | Adım 7 | Y2 | Orta (DB migration + refactor) |
| 8 | Adım 8 | Y4 | Orta (yeni mekanizma) |
| 9 | Adım 9 | O1 | Düşük (FE validasyon) |
| 10 | Adım 10 | O2 | Düşük (UI uyarı) |
| 11 | Adım 11 | O3 | Düşük (toplu replace) |
