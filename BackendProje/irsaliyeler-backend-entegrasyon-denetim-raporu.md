# İrsaliyelerPage Backend Entegrasyon Denetim Raporu

Tarih: 2026-04-15

Bu rapor, `ReactProje/src/pages/IrsaliyelerPage.jsx` sayfasının kullandığı backend akışını uçtan uca incelemek için hazırlanmıştır. İnceleme; `irsaliye`, `sipariş`, `sevkiyat planlama`, stok çıkışı ve yetkilendirme katmanlarını birlikte değerlendirir. Amaç, canlıya açılmadan önce operasyonu bozabilecek mantıksal kırıkları, frontend-backend kontrat boşluklarını ve önceki faz raporunda kapatılmış görünen maddelerle halen açık kalan riskleri ayırmaktır.

Bu çalışma analiz ve raporlama kapsamındadır; kod değişikliği içermez.

## Kapsam

İncelenen ana dosyalar:

- `ReactProje/src/pages/IrsaliyelerPage.jsx`
- `ReactProje/src/services/api.js`
- `ReactProje/src/App.jsx`
- `ReactProje/src/components/layout/Sidebar.jsx`
- `BackendProje/app/api/v1/routers/irsaliyeler.py`
- `BackendProje/app/api/v1/routers/siparisler.py`
- `BackendProje/app/api/v1/routers/sevkiyat_planlama.py`
- `BackendProje/app/application/use_cases/irsaliye_use_cases.py`
- `BackendProje/app/application/use_cases/sevkiyat_plani_use_cases.py`
- `BackendProje/app/application/dto/irsaliye_dto.py`
- `BackendProje/app/application/dto/sevkiyat_plani_dto.py`
- `BackendProje/app/infrastructure/persistence/repositories/sa_irsaliye_repository.py`
- `BackendProje/app/infrastructure/persistence/repositories/sa_sevkiyat_plani_repository.py`
- `BackendProje/app/infrastructure/persistence/mappers/siparis_lojistik_mapper.py`
- `BackendProje/app/core/services/siparis_durum_orchestrator.py`
- `BackendProje/tests/api/routers/test_siparisler_api.py`
- `BackendProje/tests/api/routers/test_sevkiyat_planlama_api.py`
- `BackendProje/tests/api/routers/test_erisim_kontrolu.py`
- `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz1.py`
- `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz2.py`
- `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz5.py`
- `BackendProje/tests/unit/use_cases/test_irsaliye_sevkiyat_transaction_use_cases.py`

## Kısa Özet

Mevcut yapı, faz raporundaki kritik teknik borçların önemli kısmını kapatmış durumda: mükerrer irsaliyenin aynı sevkiyata bağlanması engellenmiş, stok çıkışı `YuklemeOnaylaUseCase` içine taşınmış, sipariş durum orkestrasyonu eklenmiş ve zorunlu tarih alanları request DTO katmanına çekilmiş. Buna rağmen `IrsaliyelerPage` sayfası ile backend kontratı arasında halen canlıyı etkileyebilecek birkaç önemli boşluk var.

En kritik risk, `depocu` rolünün `/depocu/irsaliyeler` route'una erişebilmesine rağmen sayfanın ilk yüklemede `siparişler` ve `sevkiyat planları` endpoint'lerine gitmesi, bu iki endpoint'in ise backend'de `depocu` rolüne kapalı olmasıdır. İkinci büyük risk, irsaliye oluşturma tarafında "onaylanmış / yükleme onayı yapılmış sevkiyat planı" kuralının ne UI'da ne backend doğrulamasında açık biçimde zorlanmamasıdır. Üçüncü önemli boşluk ise backend'de hazır olan `yazdir` verisinin frontend tarafından kullanılmaması ve çıktının istemci tarafında statik veriyle üretilmesidir.

## Kritik Prod Bloklayıcılar

### 1. `depocu` route'u açık, ancak sayfa ilk yüklemede 403'e düşebilir

Durum:

- `IrsaliyelerPage` ilk yüklemede üç endpoint'i birlikte çağırıyor: `getIrsaliyeler`, `getSiparisler`, `getSevkiyatPlanlari`.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:71-76`, `:88-100`
- `/depocu/irsaliyeler` route'u depocu arayüzünde tanımlı.
  Kanıt: `ReactProje/src/App.jsx:91-99`
- `irsaliyeler` read endpoint'i `depocu` rolüne açık.
  Kanıt: `BackendProje/app/api/v1/routers/irsaliyeler.py:43`, `:53`, `:84`
- `siparişler` ve `sevkiyat-planlama` endpoint'leri yalnızca `admin` ve `lojistik` rollerine açık.
  Kanıt: `BackendProje/app/api/v1/routers/siparisler.py:50-81`, `BackendProje/app/api/v1/routers/sevkiyat_planlama.py:46-90`
- API testleri `depocu` için bu iki endpoint'te 403 beklediğini doğruluyor.
  Kanıt: `BackendProje/tests/api/routers/test_siparisler_api.py:117-120`, `BackendProje/tests/api/routers/test_sevkiyat_planlama_api.py:113-116`, `BackendProje/tests/api/routers/test_erisim_kontrolu.py:42-51`

Etkisi:

- Depocu kullanıcı route'a URL üzerinden erişebilir, ancak ilk veri yüklemesinde sayfa kırılır.
- Sidebar bu menüyü depocuya göstermese de route açık olduğu için problem gerçek kullanımda ortaya çıkabilir.
  Kanıt: `ReactProje/src/components/layout/Sidebar.jsx:61-64`

Değerlendirme:

- Bu durum bir UI görünürlük problemi değil, route/permission kontrat tutarsızlığıdır.
- Canlı öncesi çözülmeden bırakılmamalıdır.

### 2. İrsaliye oluşturma akışında sevkiyat planı durumu zorlanmıyor

Durum:

- UI metni "onaylanmış sevkiyat planları üzerinden" irsaliye üretildiğini söylüyor.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:507`
- Ancak `kullanilabilirPlanlar` sadece "bu plana daha önce irsaliye bağlandı mı" filtresi yapıyor.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:319-322`
- Backend `IrsaliyeOlusturUseCase`, plan var mı, aynı siparişe mi ait, aynı sevkiyata daha önce irsaliye kesilmiş mi kontrollerini yapıyor; fakat plan durumunu doğrulamıyor.
  Kanıt: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:104-113`, `:140-152`
- Stok çıkışının tek yetkili komutu `YuklemeOnaylaUseCase`; bu komut yalnızca `Planlandi` durumundaki planlar için çalışıyor.
  Kanıt: `BackendProje/app/application/use_cases/sevkiyat_plani_use_cases.py:245-282`

Etkisi:

- `Planlandi` durumundaki plan için irsaliye kesilebilir, ama stok çıkışı henüz yapılmamış olabilir.
- Sonuçta sistemde "evrak üretildi / fiziksel yükleme onayı verilmedi" gibi gri bir ara durum oluşur.

Değerlendirme:

- Faz raporundaki eski "irsaliye stok çıkışı yapıyor" sorunu kapanmış, ama bunun yerine "irsaliye yalnızca yükleme onaylı planlardan doğmalı mı" sorusu açık kalmıştır.
- Bu artık teknik bug değil, açık tanımlanmamış iş kuralı boşluğudur; yine de canlıda yanlış operasyon akışı doğurabilir.

## Mantıksal ve Akışsal İyileştirme Alanları

### 3. Sayfa aynı referans verileri gereksiz şekilde tekrar tekrar çekiyor

Durum:

- Arama metni veya durum filtresi değiştiğinde `verileriGetir` yeniden üretiliyor ve üç endpoint tekrar çağrılıyor.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:71-79`, `:88-100`
- Bu sırada sipariş ve sevkiyat listeleri her aramada yeniden çekiliyor, oysa sayfa bunları çoğunlukla lookup amaçlı kullanıyor.

Etkisi:

- Gereksiz backend yükü oluşur.
- Ağ gecikmesi arttığında sayfa hissedilir biçimde ağırlaşır.

Değerlendirme:

- Bu alan prod bloklayıcı değil, ama sayfa ölçeği büyüdükçe ilk hissedilen performans problemine dönüşür.

### 4. Backend arama mantığı ile frontend arama mantığı aynı değil

Durum:

- Backend `arama` filtresini yalnızca `irsaliye_no` ve `tir_plaka` üzerinde uyguluyor.
  Kanıt: `BackendProje/app/infrastructure/persistence/repositories/sa_irsaliye_repository.py:29-33`
- Frontend ise müşteri adı ve sipariş numarasını da arama kapsamına dahil ediyor.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:299-317`

Etkisi:

- Kullanıcı müşteri adıyla arama yaptığında frontend filtrelemesi geniş, backend ön filtresi dar kalıyor.
- `limit: 100` öncesi backend filtreleme devreye girdiği için bazı kayıtlar hiç gelmeyebilir.

Değerlendirme:

- Bu alan doğruluk problemi yaratır; kullanıcı araması her zaman "gerçek veri kümesi" üzerinde çalışmaz.

### 5. Limit bağımlılığı ve sayfalama eksikliği sessiz veri kaybı yaratabilir

Durum:

- Sayfa `irsaliyeler` için `limit: 100`, `siparişler` ve `sevkiyat planları` için `limit: 500` ile çalışıyor.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:74-76`
- UI'da sayfalama veya "daha fazla yükle" davranışı yok.

Etkisi:

- Veri sayısı eşiklerin üstüne çıktığında kullanıcı eksik veriyle çalıştığını fark etmeyebilir.
- Özellikle seçilebilir sevkiyat planları ve sipariş sözlüğü eksik kalabilir.

Değerlendirme:

- Bu problem ilk canlı açılışta değil ama veri büyüdüğünde operasyonel hataya dönüşme potansiyeline sahip.

### 6. DTO kontratı, backend'in zaten bildiği özet verileri frontend'e taşımıyor

Durum:

- `sa_irsaliye_repository` kayıtları `joinedload(IrsaliyeORM.siparis)` ile çekiyor.
  Kanıt: `BackendProje/app/infrastructure/persistence/repositories/sa_irsaliye_repository.py:23`, `:44`
- `sa_sevkiyat_plani_repository` de sipariş ve kalemleri eager load ediyor.
  Kanıt: `BackendProje/app/infrastructure/persistence/repositories/sa_sevkiyat_plani_repository.py:27-28`, `:45-46`, `:54-55`
- Ancak response DTO tarafı `IrsaliyeResponseDTO` ve `SevkiyatPlaniResponseDTO` içinde sipariş özetini taşımıyor; frontend ayrıca sipariş listesi çekmek zorunda kalıyor.
  Kanıt: `BackendProje/app/application/dto/irsaliye_dto.py:78-100`, `BackendProje/app/application/dto/sevkiyat_plani_dto.py:124-149`

Etkisi:

- Tek bir liste ekranı için üç ayrı endpoint ihtiyacı doğuyor.
- Frontend veri birleştirme mantığı büyüyor ve sayfa permission farklarından daha kolay etkileniyor.

Değerlendirme:

- Bu alan doğrudan bug değil; ancak mevcut permission çatışmasının temel sebeplerinden biri de bu tasarım.

### 7. Numara üretimi hâlâ yarış koşulu riski taşıyor

Durum:

- İrsaliye numarası son kayıt okunup bir artırılarak üretiliyor.
  Kanıt: `BackendProje/app/infrastructure/persistence/repositories/sa_irsaliye_repository.py:76-85`
- Benzer mantık sipariş tarafında da mevcut.

Etkisi:

- Eşzamanlı yoğun kullanımda benzersizlik ihlali yaşanabilir.
- Faz raporundaki önceki hataların çoğu kapanmış olsa da bu alan hâlâ "yük altında" risk taşır.

Değerlendirme:

- Orta seviye, sistem büyüdükçe önem kazanan residual risktir.

## Backend'de Hazır Olup Frontend'e Taşınmamış Yapılar

### 8. `GET /api/irsaliyeler/{id}/yazdir` endpoint'i hazır, fakat UI bunu kullanmıyor

Durum:

- Backend yazdırma endpoint'i mevcut.
  Kanıt: `BackendProje/app/api/v1/routers/irsaliyeler.py:81-85`
- Use case, `irsaliye + sipariş + kalemler` döndürüyor.
  Kanıt: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:247-305`
- DTO da bu veri sözleşmesini tanımlıyor.
  Kanıt: `BackendProje/app/application/dto/irsaliye_dto.py:142-147`
- Frontend servis katmanında `getIrsaliyeYazdirVerisi` tanımlı.
  Kanıt: `ReactProje/src/services/api.js:377`
- Ancak `IrsaliyelerPage` bu çağrıyı kullanmıyor; kendi içinde statik HTML üretiyor ve tek satırlık placeholder içerik basıyor.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:154-287`

Etkisi:

- Yazdırılan evrak backend'deki gerçek sipariş kalemlerinden kopuk olabilir.
- Resmi çıktı ile sistem verisi arasında sapma oluşur.

Değerlendirme:

- Bu alan canlı öncesi mutlaka gözden geçirilmeli; çünkü kullanıcıya görünen belge katmanı teknik doğruluktan ayrışıyor.

### 9. "Kullanılabilir sevkiyat planı" kuralı backend kontratına taşınmamış

Durum:

- Frontend kullanılabilir planları kendi içinde hesaplıyor.
  Kanıt: `ReactProje/src/pages/IrsaliyelerPage.jsx:319-322`
- Backend ise sadece temel doğrulama yapıyor; "hangi planlar irsaliye için uygundur" bilgisini ayrı bir kontrat olarak sunmuyor.

Etkisi:

- İş kuralı UI içinde dağınık kalıyor.
- Başka istemciler aynı kuralı farklı yorumlayabilir.

Değerlendirme:

- Bu alan orta vadede API tasarımına taşınmalıdır.

## Önceki Faz Raporunda Kapanmış Görünen Maddeler

Mevcut `cikis-akis-raporu.md` ile karşılaştırıldığında aşağıdaki maddelerin önemli ölçüde kapandığı görülüyor:

### Kapanan 1. Mükerrer irsaliye ile mükerrer stok çıkışı riski

- İrsaliye oluşturma use case'i artık aynı sevkiyata ikinci irsaliyeyi reddediyor.
  Kanıt: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:150-152`
- Testler bunu doğruluyor.
  Kanıt: `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz1.py:146`, `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz2.py:190-226`

### Kapanan 2. Sevkiyat planının ileri durumda açılması

- `SevkiyatPlaniOlusturRequestDTO` artık sadece `Planlandi` kabul ediyor.
  Kanıt: `BackendProje/app/application/dto/sevkiyat_plani_dto.py:44-58`
- Faz 1 testleri bu kuralı doğruluyor.
  Kanıt: `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz1.py:5`, `:91`

### Kapanan 3. Stok çıkışının irsaliye içinden tetiklenmesi

- `IrsaliyeOlusturUseCase` yorum ve akış olarak evrak üretimine indirgenmiş.
  Kanıt: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:81-84`
- `YuklemeOnaylaUseCase` stok çıkışının tek yetkili komutu haline gelmiş.
  Kanıt: `BackendProje/app/application/use_cases/sevkiyat_plani_use_cases.py:245-257`
- Faz 2 testleri bunu doğruluyor.
  Kanıt: `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz2.py:5-8`, `BackendProje/tests/unit/use_cases/test_irsaliye_sevkiyat_transaction_use_cases.py:6`

### Kapanan 4. `sevkiyat_id` varlık ve sipariş uyumu doğrulaması

- Use case artık planın varlığını, sipariş uyumunu ve aynı sevkiyata ikinci irsaliye üretimini birlikte doğruluyor.
  Kanıt: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:140-152`

### Kapanan 5. Nihai irsaliye kaydının serbestçe düzenlenebilmesi

- `IrsaliyeGuncelleUseCase`, alan değişikliği varsa `duzenlenebilir_mi()` kontrolü yapıyor.
  Kanıt: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:191-200`
- Faz testleri de düzenlenebilirlik davranışını kapsıyor.
  Kanıt: `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz1.py:164-202`, `BackendProje/tests/unit/use_cases/test_cikis_akisi_faz5.py:35`

### Kapanan 6. Sipariş durumlarının sevkiyatla tamamen kopuk olması

- `SiparisDurumOrchestrator` artık sevkiyat olaylarından sipariş durumu türetiyor.
  Kanıt: `BackendProje/app/core/services/siparis_durum_orchestrator.py:21-69`

## Canlı Öncesi Test ve Güvence Boşlukları

### 10. `irsaliyeler` endpoint ailesi için yetki matrisi testleri eksik

Durum:

- Genel erişim kontrol testleri `siparişler` ve `sevkiyat-planlama` için açık, ancak `irsaliyeler` endpoint ailesi bu matriste görünmüyor.
  Kanıt: `BackendProje/tests/api/routers/test_erisim_kontrolu.py:42-70`

Etkisi:

- `depocu` read, `lojistik/admin` write gibi daha ince permission kuralları zamanla sessizce bozulabilir.

### 11. Frontend route + permission entegrasyonu için senaryo testi yok

Durum:

- API seviyesinde 403 testleri var, fakat `/depocu/irsaliyeler` sayfasının gerçek yükleme davranışını kontrol eden bir UI veya entegrasyon testi görünmüyor.

Etkisi:

- Route açık, backend kapalı gibi çapraz sistem problemleri testlerden kaçıyor.

### 12. Yazdırma bütünlüğü testlenmiyor

Durum:

- Backend yazdırma DTO'su var, frontend kendi HTML'ini üretiyor; iki çıktı arasında tutarlılık testi görünmüyor.

Etkisi:

- Belge çıktısındaki veri sapması prod'a kadar fark edilmeyebilir.

## Sonuç ve Önceliklendirme

Canlı öncesi en yüksek öncelikli üç konu:

1. `depocu` erişim akışındaki route/backend permission çakışmasını kapatmak.
2. İrsaliye oluşturmanın yalnızca hangi sevkiyat durumlarında mümkün olduğunu açık iş kuralına bağlamak.
3. Yazdırma akışını backend'in gerçek `yazdir` verisiyle hizalamak.

Bunların hemen ardından ele alınması gereken ikinci grup konular:

- Arama kontratını backend ve frontend arasında hizalamak.
- Liste ekranlarını `limit` bağımlılığından kurtarmak veya görünür pagination eklemek.
- İrsaliye ve sevkiyat response'larına minimum sipariş özeti ekleyerek üçlü fetch bağımlılığını azaltmak.
- `irsaliyeler` endpoint ailesi için yetki matrisini testlere eklemek.

## Önerilen Sonraki Adımlar

- Ürün kararı: `depocu` rolü `IrsaliyelerPage` ekranını gerçekten kullanacak mı, kullanmayacak mı netleştirilmeli.
- İş kuralı kararı: İrsaliye yalnızca `yukleme onayı verilmiş` planlardan mı üretilecek, yoksa `Planlandi` aşamasında da üretime izin var mı karar altına alınmalı.
- Teknik karar: Yazdırma ekranı client-side taslak çıktı mı olacak, yoksa backend'in otoriter `yazdir` kontratı mı kullanılacak belirlenmeli.
- API iyileştirmesi: İrsaliye ve sevkiyat liste response'larına sipariş özeti ve gerekli durum bilgileri eklenerek frontend bağımlılıkları sadeleştirilmeli.
