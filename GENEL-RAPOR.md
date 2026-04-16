📊 Depo Yönetim Sistemi – Endüstri Standardı Analizi

Bu belge, ürün kapsamı ve öncelik sorularına verilen yanıtlar sonrası güncellenmiş final analiz raporudur. Amaç; mevcut güçlü yönleri, canlıya geçiş için kritik eksikleri ve karar netliği kazanmış uygulama yol haritasını tek yerde toplamak.

Not: Bu revizyon yalnızca dokümantasyon kapsamındadır. Runtime API, veri şeması veya uygulama arayüzlerinde doğrudan bir değişiklik tanımlamaz.

## Yönetici Özeti

- Sistem, Türkiye odaklı ve tek şirket içi kullanılan genel amaçlı bir WMS olarak konumlandırılmaktadır.
- ERP; ürün ve sipariş master verisinin kaynağı, WMS ise depo operasyon katmanıdır.
- Canlıya geçiş için minimum kabul edilebilir kapsam `Faz 1 + Faz 2` olarak belirlenmiştir.
- FEFO desteklenmelidir; ancak ilk sürümde yetkili kullanıcı için override edilebilir yapı tercih edilmektedir.
- 3PL / multi-tenant, kitting / bundle ve offline mobil terminal ilk sürüm kapsamı dışındadır.

## Güçlü Yönler

### Mimari

- Clean Architecture %100 tamamlanmış (17/17 modül); domain, application ve infrastructure ayrımı net.
- Domain entity'lerde iş kuralları, state machine'ler ve geçiş validasyonları doğru katmanda konumlanmış.
- DI container, repository pattern ve use case katmanı temiz bir yapı sunuyor.
- ERP entegrasyonu için Adapter Pattern kullanımı doğru mimari tercih.

### Domain Modeli

- Lot, Palet, Raf ve Zon hiyerarşisi endüstri standardına uygun.
- Depolama tipi ile zon tipi uyumluluk matrisi tanımlı.
- Hiyerarşik raf kodu yapısı lokasyon izlenebilirliğini destekliyor.
- Putaway görev akışı ve override mantığı mevcut.
- Sevkiyat ve sipariş state machine'leri ayrı tutulmuş, orkestrasyon mantığı kurulmuş.
- Palet bazlı stok hareketi takibi mevcut.

### Güvenlik ve Altyapı

- JWT + refresh token rotation, bcrypt ve rate limiting altyapısı hazır.
- Rol bazlı ve depo bazlı erişim kontrolü bulunuyor.
- Birleşik exception handler ve SistemLog audit yaklaşımı mevcut.

---

## Netleşen Ürün Kararları

- Ürün odağı, Türkiye odaklı ve tek şirket içi kullanılan genel bir WMS'tir; ana kapsam mal kabul, yerleştirme, stok yönetimi ve sevkiyat süreçleridir.
- 3PL / multi-tenant mimari ilk sürüm hedefi değildir.
- Sert regülasyonlu gıda veya ilaç dikeyi hedeflenmemektedir; buna rağmen lot ve SKT takibi ile FEFO desteği hazır olmalıdır.
- E-İrsaliye önemli bir ihtiyaçtır; ancak ilk çekirdek sürüm için zorunlu değildir.
- E-İrsaliye ve ERP entegrasyonları sağlayıcıdan bağımsız adapter mantığında tasarlanmalıdır.
- ERP ana master sistem değildir; ürün ve sipariş master verilerinin ERP'den gelmesi, WMS'in depo içi operasyonları ve stok hareketlerini yönetmesi hedeflenmektedir.
- Toplama akışı palet bazlı olacaktır; koli veya adet bazlı picking ilk sürüm kapsamına dahil değildir.
- Sevkiyat kalemleri operasyon tarafında belirli paletlere atanmış Pick Task'lara dönüştürülmelidir.
- FEFO, sevkiyatta varsayılan seçim kuralı olmalıdır; ancak yetkili kullanıcı için override edilebilir olmalı ve tüm override işlemleri audit log ile izlenmelidir.
- Rezervasyon, sipariş `Hazırlanıyor` durumuna geçtiğinde başlamalı; fiziksel stok düşümü ise sevkiyat kesinleştiğinde yapılmalıdır.
- Rezervasyon iptal veya değişiklik durumunda geri alınabilmelidir.
- Cycle count, dock randevu ve gelişmiş operasyon yönetimi ilk çekirdek sürüm için öncelikli değildir.
- İlk hedef orta ölçekli depo operasyonlarıdır; sistem birden fazla eşzamanlı operatörü güvenli şekilde desteklemeli, ancak hiper-ölçek varsayımıyla tasarlanmamalıdır.
- Kitting / bundle ilk sürüm kapsamı dışındadır.
- Offline mobil terminal zorunlu değildir; ilk sürüm online-first çalışmalı, ancak mimari ileride offline desteğe açık bırakılmalıdır.
- Canlıya geçiş kritiği `Faz 1 + Faz 2`dir. Slotting optimization, Faz 3'e çekilmiş orta öncelikli bir farklılaştırıcıdır.

---

## Önceliklendirilmiş Gelişim Alanları

### MVP Kritik

- FEFO destekli toplama: Sevkiyatta palet ve lot seçimi FEFO önceliğiyle yapılmalı, gerektiğinde yetkili override desteklenmelidir.
- Palet bazlı Pick Task modeli: Sevkiyat kalemleri, operasyonel toplama görevlerine dönüştürülmelidir.
- Stok rezervasyonu / allocation: Sipariş `Hazırlanıyor` aşamasında palet tahsisi yapılmalı, uygun stok ile rezerve stok ayrımı netleştirilmelidir.
- Concurrency / locking: Aynı görevin veya paletin birden fazla operatör ya da sipariş tarafından eşzamanlı alınması engellenmelidir.
- Idempotency: Kritik POST uçlarında retry kaynaklı çift kayıt ve çift işlem riski kapatılmalıdır.
- Audit immutability: Stok hareketi ve kritik operasyon logları append-only mantığında korunmalıdır.

### Yakın Vade / Faz 3

- Slotting optimization: ABC, hız ve lokasyon mesafesi bazlı akıllı yerleştirme stratejisi eklenmelidir.
- Stok görünürlüğü ve performans: Slotting ile bağlantılı olarak uygun stok görünürlüğü ve stok hesaplama performansı iyileştirilmelidir.

### Roadmap

- RMA / reverse logistics süreci
- Karantina ile bağlı kalite kontrol workflow'u
- ABC tabanlı cycle count planlaması
- Depo-arası transfer süreci
- Gelişmiş outbound KPI dashboard'u
- Dock / kapı randevu ve çakışma yönetimi
- ERP senkronizasyonunun derinleştirilmesi
- E-İrsaliye / GİB entegrasyonu
- Operasyonel ihtiyaç oluşursa alıcı veya müşteri entity'si eklenmesi

### Teknik Sertleştirme

- `datetime.utcnow()` kullanımının `datetime.now(timezone.utc)` ile değiştirilmesi
- `JWT_SECRET_KEY` fallback'inin kaldırılması ve environment zorunluluğu
- CORS yapılandırmasının environment tabanlı hale getirilmesi
- Europe/Istanbul zaman dilimi tutarlılığının netleştirilmesi
- Refresh token replay korumasının güçlendirilmesi
- Şifre politikası ve opsiyonel MFA gereksinimlerinin netleştirilmesi

### Bilinçli Kapsam Dışı / Sonraya Bırakılan

- Multi-tenant / 3PL mimari
- Kitting / bundle / BOM
- Offline mobil terminal
- Koli veya adet bazlı picking
- Wave, batch ve zone picking gibi ileri toplama optimizasyonları

---

## Uygulama Yol Haritası

### Faz 1 — MVP Outbound Core

- ToplamaGorevi (Pick Task) domain modeli ve durum makinesi eklenir.
- Sevkiyat kalemlerinden palet bazlı Pick Task üretim akışı kurulur.
- FEFO öncelikli palet ve lot seçim servisi geliştirilir.
- FEFO override işlemleri için neden, kullanıcı ve zaman bilgisi audit log'a alınır.
- Sipariş `Hazırlanıyor` durumuna geçtiğinde rezervasyon başlatılır.
- Rezervasyon iptal, değişiklik ve sevkiyat kesinleşme senaryolarında yaşam döngüsü netleştirilir.
- Uygun stok ve rezerve stok ayrımı görünür hale getirilir.
- Toplama onay ekranları ve temel mobil/masaüstü operasyon akışı tamamlanır.
- FEFO seçimi ve rezervasyon çatışmaları için testler yazılır.

### Faz 2 — MVP Veri Bütünlüğü

- Görev atama ve kritik stok işlemlerinde DB seviyesinde locking uygulanır.
- Kritik POST uçlarına `Idempotency-Key` desteği eklenir.
- Stok hareketleri ve audit kayıtları immutable hale getirilir.
- Refresh token replay tespiti ile oturum kapatma davranışı tanımlanır.
- Eşzamanlı operatör ve retry senaryoları test edilir.

### Faz 3 — Operasyonel Optimizasyon

- Slotting optimization, orta öncelikli farklılaştırıcı olarak uygulanır.
- ABC sınıfı, hareket hızı ve lokasyon mesafesi bazlı yerleştirme stratejisi eklenir.
- Stok görünürlüğü ve stok hesaplama performansı gerektiğinde cache veya materialized yaklaşımıyla iyileştirilir.

### Faz 4 — Fonksiyonel Roadmap

- RMA süreci kurulur.
- Kalite kontrol ve karantina workflow'u tamamlanır.
- Cycle count yapısı operasyon ölçeği büyüdükçe ABC bazlı hale getirilir.
- Depo-arası transfer akışı eklenir.
- Dock randevu yönetimi ve outbound KPI dashboard'u ileriki operasyon ihtiyacına göre eklenir.
- Gerekirse tenant mantığından bağımsız müşteri / alıcı firma modeli eklenir.

### Faz 5 — Entegrasyon Roadmap

- ERP ile ürün ve sipariş master veri akışları adapter tabanlı olarak derinleştirilir.
- E-İrsaliye için sağlayıcıdan bağımsız entegrasyon katmanı tasarlanır.
- GİB alanları, arşivleme ve yanıt takibi için belge modeli genişletilir.

### Faz 6 — Teknik Sertleştirme

- UTC kullanım standardı güncellenir.
- Güvenlik yapılandırmaları environment-first hale getirilir.
- Zaman dilimi, parola politikası ve token güvenliği sertleştirilir.
- Operasyon ölçeği büyüdükçe ek güvenlik ve performans iyileştirmeleri devreye alınır.

---

## Canlıya Geçiş Kararı

- Canlıya geçiş için zorunlu minimum kapsam `Faz 1 — MVP Outbound Core` ve `Faz 2 — MVP Veri Bütünlüğü` tamamlanmış olmalıdır.
- Faz 3 ve sonrası, sistemi rekabetçi ve ölçeklenebilir hale getiren yakın vade ve roadmap yatırımlarıdır.
- E-İrsaliye, RMA, QC, cycle count ve gelişmiş KPI başlıkları mimari olarak desteklenebilir tutulmalı; ancak ilk release blocker olarak değerlendirilmemelidir.

## Faz 1 ve Faz 2 TAMAMLANDI.✅
