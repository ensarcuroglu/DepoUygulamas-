# Is Akisi Raporu

Tarih: 2026-03-30
Kapsam: Kritik WMS backend akislarinin mimari ve operasyonel incelemesi

## 1. Amac ve Kapsam

Bu rapor, `BackendProje` altindaki kritik depo yonetimi backend akislarini analiz eder. Inceleme ozellikle su alanlara odaklanmistir:

- Palet bazli stok girisi ve cikisi
- Mal kabul irsaliyesi akis mantigi
- Irsaliye olusturma ve sevkiyat stok cikisi
- Auth ve transaction yonetimi
- Performans ve test guvenceleri

Inceleme CRUD seviyesinde tam tarama degil, is akislarinin tutarliligi ve uretim riski uzerine odakli bir mimari denetimdir.

## 2. Mevcut Is Akisi Ozeti

### 2.1 Palet bazli giris

Akis su sekilde calisiyor:

1. `POST /api/stok-islemleri/palet-giris` istegi router seviyesinde aliniyor: `BackendProje/app/api/v1/routers/stok_islemleri.py:34-61`
2. `PaletBazliStokDomainService.palet_giris()` palet bilgisini adapter uzerinden getiriyor, lot ve palet olusturuyor, stok hareketi yaziyor: `BackendProje/app/core/services/palet_bazli_stok_domain_service.py:46-120`
3. Adapter, mal kabul kaleminden veri okuyup kalem durumunu `GirisYapildi` yapiyor: `BackendProje/app/infrastructure/services/irsaliye_palet_veri_kaynagi_service.py:41-111`
4. Router sonunda `db.commit()` cagiriyor: `BackendProje/app/api/v1/routers/stok_islemleri.py:52-61`

### 2.2 Palet bazli cikis

1. Router `palet_no` ve opsiyonel `miktar` ile istegi aliyor: `BackendProje/app/api/v1/routers/stok_islemleri.py:64-87`
2. `PaletBazliStokDomainService.palet_cikis()` tam veya kismi cikis yapiyor: `BackendProje/app/core/services/palet_bazli_stok_domain_service.py:124-197`
3. Cikis sonrasi stok hareketi ve sistem logu yaziliyor
4. Router sonunda `db.commit()` cagiriyor

### 2.3 Irsaliye olusturma

1. `IrsaliyeOlusturUseCase` siparisi yukluyor, irsaliye numarasi uretiyor ve kaydi olusturuyor: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:78-149`
2. Sevkiyat tarafinda stok daha once dusulmemisse `StokCikisDomainService.siparis_bazli_stok_cikisi()` cagriliyor: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:139-147`
3. Use case kendi `db.commit()` cagrisi ile islemi bitiriyor: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:149`

### 2.4 Sevkiyat yukleme akisi

1. `SevkiyatPlaniGuncelleUseCase` durum degisimini yapiyor: `BackendProje/app/application/use_cases/sevkiyat_plani_use_cases.py:131-225`
2. Durum ilk kez `Yukleniyor` oluyorsa siparis bazli FIFO stok cikisi tetikleniyor: `BackendProje/app/application/use_cases/sevkiyat_plani_use_cases.py:207-218`
3. Use case sonunda `db.commit()` cagiriliyor: `BackendProje/app/application/use_cases/sevkiyat_plani_use_cases.py:220`

### 2.5 Auth / refresh token akisi

1. Login sonrasi refresh token hash'i kullanici kaydina yaziliyor: `BackendProje/app/api/v1/routers/auth.py:36-72`
2. Refresh token dogrulamasi tum kullanicilar uzerinde lineer tarama ile yapiliyor: `BackendProje/auth.py:112-143`

## 3. Kritik Bulgular

### Kritik-1: Siparis bazli stok cikisi hata verdiginde akis basarisiz olmuyor, sadece log yaziliyor

Kanıt:

- `StokCikisDomainService.siparis_bazli_stok_cikisi()` icinde stok uyumsuzlugu yakalaniyor ve exception tekrar firlatilmiyor: `BackendProje/app/core/services/stok_cikis_domain_service.py:52-78`
- Ayni servis, siparis kalemlerini tek tek geziyor ve sorunlu kalemden sonra akisa devam ediyor: `BackendProje/app/core/services/stok_cikis_domain_service.py:55-79`

Sorun:

- Yetersiz stok veya FIFO tutarsizligi olan bir urunde fiziksel stok dusmeden irsaliye ya da sevkiyat akisi "basarili" tamamlanabilir.
- Daha kotusu, onceki kalemlerde stok dusulmus, sonraki kalemde hata olusmus olabilir; buna ragmen ust akis exception almiyorsa belge ve stok durumu birbiriyle uyusmaz.

Etki:

- Kismi stok dusumu
- Hatali irsaliye kesimi
- Sevkiyat planinin gercekte hazir olmayan siparisi yukleniyor gibi davranmasi
- Operasyonda sayim farki ve sevk hatasi

Oneri:

- `StokVeriUyumsuzluguError` loglanip yutulmamali, ust akisa propagate edilmeli
- Siparis bazli cikis butun kalemler icin atomik basarisizlik modeliyle calismali
- Hata logu korunabilir ama exception mutlaka yeniden firlatilmali

### Kritik-2: Repository katmanindaki erken `commit()` cagirilari transaction atomikligini bozuyor

Kanıt:

- `IrsaliyeOlusturUseCase` transaction'i kendi yonettigini varsayiyor: `BackendProje/app/application/use_cases/irsaliye_use_cases.py:126-153`
- Ama `SqlAlchemyIrsaliyeRepository.olustur()` kaydi use case bitmeden commit ediyor: `BackendProje/app/infrastructure/persistence/repositories/sa_irsaliye_repository.py:48-54`
- `SevkiyatPlaniGuncelleUseCase` de benzer sekilde kendi `db.commit()` / `rollback()` bloklarina sahip: `BackendProje/app/application/use_cases/sevkiyat_plani_use_cases.py:193-224`
- Buna ragmen `SqlAlchemySevkiyatPlaniRepository.guncelle()` ic commit yapiyor: `BackendProje/app/infrastructure/persistence/repositories/sa_sevkiyat_plani_repository.py:58-75`
- Ayni anti-pattern mal kabul repository'sinde de var: `BackendProje/app/infrastructure/persistence/repositories/sa_mal_kabul_irsaliye_repository.py:69-77`

Sorun:

- Use case transaction sinirlarini kontrol ediyor gibi gorunuyor ama repository icindeki commit'ler bu garanti bozuyor.
- Sonraki adim hata verirse use case tarafindaki `rollback()` daha once commit edilmis kayitlari geri alamaz.

Etki:

- Irsaliye kaydi basarili, stok dusumu basarisiz gibi yarim kalmis durumlar
- Sevkiyat durumu guncellenmis, stok hareketleri eksik gibi tutarsizliklar
- Uretimde geri donusu zor veri bozulmalari

Oneri:

- Repository metotlari varsayilan olarak `flush()` yapmali, `commit()` yapmamali
- Transaction siniri use case veya Unit of Work katmaninda toplanmali
- `auto_commit=False` deseni tum yazma repository'lerinde tutarli hale getirilmeli

### Kritik-3: Onaysiz mal kabul kalemlerinden stok girisine izin veriliyor

Kanıt:

- `IrsaliyePaletVeriKaynagiService.palet_bilgisi_getir()` kalemi ve bagli irsaliyeyi yukluyor ama irsaliye durumunu kontrol etmiyor: `BackendProje/app/infrastructure/services/irsaliye_palet_veri_kaynagi_service.py:41-90`
- `palet_giris_onayla()` da yine sadece kalem durumuna bakiyor, irsaliyenin `Onaylandi` olup olmadigini dogrulamiyor: `BackendProje/app/infrastructure/services/irsaliye_palet_veri_kaynagi_service.py:92-111`
- Oysa domain entity acikca "onaylandiktan sonra stok girisine hazir" modelini tarif ediyor: `BackendProje/app/core/entities/mal_kabul_irsaliye.py:75-84`

Sorun:

- Taslak haldeki mal kabul belgesine bagli paletler sisteme alinabilir.
- Bu, belge onayi ile fiziksel kabul arasindaki kontrol noktasini ortadan kaldiriyor.

Etki:

- Onaysiz tedarik kabulunden stok yaratma
- Yanlis belge ile stok olusumu
- ERP entegrasyonunda source-of-truth sapmasi

Oneri:

- Adapter seviyesinde `irsaliye.durum == Onaylandi` zorunlu hale getirilmeli
- Taslak belge icin `GecersizIslemError` donulmeli
- Bu kurala API testi eklenmeli

## 4. Yuksek Oncelikli Bulgular

### Yuksek-1: Tum kalemler girildiginde mal kabul irsaliyesi otomatik `Tamamlandi` olmuyor

Kanıt:

- Domain entity, tum kalemler girildiginde `tamamla()` ile `Tamamlandi` durumuna gecebilme kuralini tanimliyor: `BackendProje/app/core/entities/mal_kabul_irsaliye.py:86-105`
- Ayrica `tum_kalemler_girildi_mi()` ve `bekleyen_kalem_sayisi()` yardimcilari da mevcut: `BackendProje/app/core/entities/mal_kabul_irsaliye.py:121-126`
- Ancak palet girisi akisinda kalem `GirisYapildi` olduktan sonra irsaliye seviyesinde tamamlanma kontrolu yapilmiyor: `BackendProje/app/infrastructure/services/irsaliye_palet_veri_kaynagi_service.py:92-111`

Sorun:

- Is akisi tamamlanmis olsa bile belge durumu geride kaliyor.
- Raporlama ve operasyon ekranlari "bekleyen" gibi gorunen ama fiilen bitmis mal kabulleri gosterebilir.

Etki:

- Yanlis operasyonel dashboard
- Manuel durum duzeltme ihtiyaci
- ERP/WMS senkronizasyonunda durum uyusmazligi

Oneri:

- `palet_giris_onayla()` icinde ilgili kalem guncellendikten sonra `tum_kalemler_girildi_mi()` kontrol edilmeli
- Tum kalemler tamamlandiysa irsaliye `Tamamlandi` durumuna alinmali

### Yuksek-2: Refresh token dogrulamasi kullanici sayisi arttikca pahali hale gelecek

Kanıt:

- `verify_and_get_user_from_refresh_token()` once tum kullanicilari cekiyor, sonra her biri icin bcrypt verify deniyor: `BackendProje/auth.py:112-143`

Sorun:

- Bu algoritma O(n) kullanici taramasi yapiyor.
- Bcrypt dogasi geregi CPU pahali; bu nedenle refresh endpoint'i kullanici sayisi buyudukce ciddi yavaslar.

Etki:

- Login/refresh gecikmeleri
- Gereksiz veritabani ve CPU tuketimi
- Basit bir trafik artisinin auth darboğazi olmasi

Oneri:

- Refresh token icin rastgele opaque token yerine indekslenebilir bir `token_id` + hash modeli kullanilmali
- Alternatif olarak token tablosu tutulup `token_id` ile noktasal lookup yapilmali
- Refresh ve logout endpoint'leri icin ayrintili test eklenmeli

### Yuksek-3: Hassas bilgi loglama ve runtime schema olusturma uretim riskini artiriyor

Kanıt:

- Uygulama baslangicinda JWT secret'in ilk 8 karakteri loglaniyor: `BackendProje/main.py:23-26`
- Uygulama boot sirasinda `Base.metadata.create_all(bind=engine)` cagriliyor: `BackendProje/main.py:159-160`

Sorun:

- Secret parcasi loglarda kalici iz birakir; dogrudan anahtar olmasa da guvenlik hijyeni acisindan zayif pratiktir.
- Runtime `create_all()` migration disiplinini bozar; staging/prod ortamlarda beklenmeyen schema drift yaratabilir.

Etki:

- Log sızıntısı riskinde ekstra hassas veri ifsasi
- Duzensiz schema yonetimi
- Migration ile runtime davranisinin ayrismasi

Oneri:

- Secret logu tamamen kaldirilmali
- Schema olusturma sadece migration araclariyla yapilmali
- Boot-time health check ile migration varligi dogrulanmali

## 5. Performans Darbogazlari

### 5.1 Mal kabul listeleme sorgusu gereksiz derecede agir

Kanıt:

- `SqlAlchemyMalKabulIrsaliyeRepository._base_query()` her durumda `kalemler`, `urun` ve `raf` iliskilerini eager load ediyor: `BackendProje/app/infrastructure/persistence/repositories/sa_mal_kabul_irsaliye_repository.py:26-32`
- Ayni agir query hem listeleme hem detay icin kullaniliyor: `BackendProje/app/infrastructure/persistence/repositories/sa_mal_kabul_irsaliye_repository.py:34-67`

Risk:

- Liste ekraninda her irsaliye icin tum kalemleri tasimak gereksiz veri maliyeti uretir
- Kalem sayisi buyudukce sorgu satir carpani ve memory kullanimi artar

Oneri:

- Liste ve detay icin ayri query profilleri tanimlanmali
- Liste ekraninda sadece header alanlari cekilmeli
- Kalemler lazim oldugunda detay endpoint'inde yuklenmeli

### 5.2 Refresh endpoint CPU agir bir tarama modeli kullaniyor

Bu konu ayni zamanda yuksek oncelikli mantiksal/performance riski oldugu icin `BackendProje/auth.py:112-143` referansi ile birlikte ayrica ele alinmistir.

## 6. Mantiksal Aciklar ve Veri Tutarliligi Riskleri

- Belge onayi ile fiziksel stok yaratma arasindaki kontrol noktasi adapter seviyesinde uygulanmiyor
- Use case transaction sinirlari repository commit'leri nedeniyle guvenilir degil
- Siparis bazli stok cikisi butunsel basarisizlik modeliyle calismadigi icin yari basarili akislara izin veriyor
- Mal kabul belge durumu ile gercek operasyon durumu birbirinden kopabiliyor

Bu dort baslik birlikte degerlendirildiginde, mevcut yapinin en zayif noktasi "islemin sonucunu tek bir gercek durum olarak koruyamamak" oluyor.

## 7. Test ve Gozlemlenebilirlik Bosluklari

### 7.1 Mevcut test guvencesi sinirli

Mevcut dogrudan gorunen test yuzeyi:

- Auth tarafinda temel login/me/register testleri var: `BackendProje/tests/api/routers/test_auth_api.py:13-113`
- Palet bazli stok islemleri icin API testleri var: `BackendProje/tests/api/routers/test_stok_islemleri_api.py:45-194`
- Palet bazli domain servis icin unit testler var: `BackendProje/tests/unit/services/test_palet_bazli_stok_domain_service.py`

Eksik veya gorunmeyen test alanlari:

- `IrsaliyeOlusturUseCase` hata yolu testleri
- `SevkiyatPlaniGuncelleUseCase` durum gecisi + stok cikisi hata yolu testleri
- Refresh token / logout davranisi
- Onaysiz mal kabulden palet girisi reddi
- Tum kalemler girildiginde mal kabul tamamlanmasi
- Concurrent palet girisi / cikisi ve duplicate request senaryolari

### 7.2 Testler yerelde calistirilamadi

Dogrulama notu:

- `python -m pytest ...` komutu mevcut ortamda `No module named pytest` hatasi verdi
- Buna ragmen test bagimliliklari `BackendProje/requirements-test.txt` icinde tanimli

Sonuc:

- Kod uzerinden statik ve mantiksal analiz yapilabildi
- Ancak mevcut bulgularin bir kismi su anda sadece kod incelemesiyle teyit edildi; otomatik test kosumu bu oturumda yapilamadi

## 8. Onceliklendirilmis Revizyon Onerileri

### P0 - Hemen ele alinmali

1. `StokCikisDomainService` icinde hata yutma davranisini kaldir
2. Yazma repository'lerinden ic `commit()` cagri modelini temizle
3. Irsaliye ve sevkiyat use case'lerini gercek atomik transaction sinirina tası

### P1 - Is akisi tutarliligi

1. Mal kabul palet girisinde belge durum kontrolu ekle
2. Tum kalemler tamamlandiginda mal kabul irsaliyesini otomatik tamamla
3. Palet girisi ve cikisi icin idempotency/duplicate request stratejisi ekle

### P1 - Guvenlik ve performans

1. Refresh token lineer tarama modelini degistir
2. Secret logunu kaldir
3. `create_all()` cagrisini migration disiplinine tasi

### P2 - Test ve izlenebilirlik

1. Irsaliye/sevkiyat hata yollarina unit ve integration test ekle
2. Refresh/logout akisini API testleriyle kapsa
3. Mal kabul durum gecisleri icin negatif testler yaz
4. Kritik transaction akislari icin structured log ve correlation id modeli ekle

## 9. Sonuc

Kod tabani iyi niyetli bir Clean Architecture ayrisimi kurmaya baslamis, ancak kritik WMS akislarinda uc temel sorun dikkat cekiyor:

- Hatalarin bazilarinin is akisini durdurmaktan cok loga donusturulmesi
- Transaction kontrolunun use case ile repository arasinda tutarsiz paylasilmasi
- Belge durumlari ile fiziksel operasyon sonucunun her zaman senkron tutulmamasi

Bu uc konu duzeltilmeden sistem buyudukce veri tutarsizligi, sevkiyat hatasi ve operasyonel guven kaybi riski artar. En dogru sonraki adim, once transaction ve hata yayilimi modelini duzeltmek; sonra mal kabul durum akisini tamamlamak; son olarak auth/performance tarafini sertlestirmektir.
