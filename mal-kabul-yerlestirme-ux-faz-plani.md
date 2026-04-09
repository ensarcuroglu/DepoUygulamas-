# Mal Kabul ve Yerleştirme UX Faz Planı

## Amaç

Bu doküman, mal kabulden rafa yerleştirmeye kadar olan depo içi akışı depocu gözünden sadeleştirmek, hataya daha dayanıklı hale getirmek ve endüstri standardına yaklaştırmak için hazırlanmıştır.

Ana hedef:

- Operatörün aynı iş için birden fazla ekran arasında karar vermek zorunda kalmaması
- Evrak durumu ile fiziksel operasyon durumunun birbirine karışmaması
- Mobil terminal akışının hızlı, net ve hataya kapalı olması
- İstisna durumlarının kullanıcıyı kilitlemeden yönetilmesi

---

## Mevcut Durumun Kısa Teşhisi

Bugünkü yapı temel olarak doğru bir omurgaya sahip olsa da kullanıcı deneyimi tarafında aşağıdaki kritik sorunlar öne çıkıyor:

1. Aynı inbound iş için iki farklı normal akış bulunuyor.
   - Mal kabul onayı sonrası palet ve yerleştirme görevi oluşturma akışı var.
   - Bunun yanında stok hareketleri ekranında hala onaylı irsaliye üzerinden toplu giriş akışı var.

2. Statü anlamları operasyonda net değil.
   - `Onaylandı`
   - `Giriş yapıldı`
   - `Tamamlandı`
   Bu kavramlar kullanıcı için tek bakışta ayrışmıyor.

3. İrsaliye, yerleştirme tamamlanmadan manuel olarak kapatılabiliyor.

4. Terminal akışı operatöre bazı adımlarda doğrulama tamamlanmadan "başarılı" hissi veriyor.

5. Sistem yer yer depocu dili yerine teknik kimlik diliyle konuşuyor.
   - `Palet ID`
   - `Hedef Raf #`
   yerine
   - `Palet Barkodu`
   - `Raf Kodu`
   - `Ürün`
   - `Miktar`
   gibi alanlar öne çıkmalı.

---

## Hedef Operasyon Modeli

İdeal standart akış aşağıdaki gibi olmalıdır:

1. Tır gelir.
2. Mal kabul görevlisi irsaliyeyi açar veya oluşturur.
3. Kabul edilen paletler sisteme alınır.
4. Sistem bu paletleri otomatik olarak `Geçici Kabul Alanı / Staging` konumuna işler.
5. Aynı anda yerleştirme görevleri oluşur.
6. Depocu sadece terminalden sıradaki görevi alır.
7. Paleti doğrular, rafı okutur, yerleştirir.
8. Tüm ilişkili görevler tamamlanınca irsaliye otomatik kapanır.

Bu modelde operatörün zihnindeki akış çok nettir:

`Kabul et -> Geçici alana indir -> Görev al -> Rafa koy -> Bitir`

---

## Tasarım Prensipleri

Bu geliştirmeler boyunca şu prensipler korunmalıdır:

1. Tek iş, tek ana akış
2. Teknik statü değil, operasyonel anlam
3. Her ekranda "bir sonraki doğru aksiyon" net görünmeli
4. Hata mesajı sadece hatayı değil, ne yapılacağını da söylemeli
5. Mobil terminal, en düşük eğitim seviyesiyle bile kullanılabilmeli
6. İstisna durumları normal akıştan ayrı ama kolay erişilebilir olmalı

---

## Faz 1 - Akışın Sadeleştirilmesi ve Statü Modelinin Düzeltilmesi ✅ TAMAMLANDI

### Amaç

Normal inbound sürecini tek akışta toplamak ve statüleri saha diline uygun hale getirmek.

### Yapılacaklar

1. `Stok Hareketleri > Toplu Giriş` akışını normal depocu kullanımından çıkart.
   - Bu ekran sadece istisna, veri düzeltme veya migrasyon senaryoları için kullanılmalı.
   - Gerekirse rol bazlı görünürlük uygulanmalı.

2. Mal kabul onayı sonrası sistemin "bir sonraki adımı" açıkça göstermesini sağla.
   - Örnek:
   - `12 palet kabul edildi`
   - `12 yerleştirme görevi oluşturuldu`
   - `Yerleştirmeye başla`

3. Evrak durumu ile operasyon durumunu ayır.

   Önerilen ayrım:

   - Evrak durumu:
     - `Taslak`
     - `Onaylı`
     - `Kapandı`

   - Operasyon durumu:
     - `Stagingde`
     - `Yerleştirme Bekliyor`
     - `Yerleştirme Devam Ediyor`
     - `Yerleştirme Tamamlandı`
     - `İstisna Var`

4. `Tamamlandı` butonunu kullanıcı ekranından kaldır.
   - İrsaliye manuel değil, iş kurallarıyla kapanmalı.

5. İrsaliye kapanış kuralını netleştir.
   - Tüm ilgili paletler yerleştirme açısından kapanmadan irsaliye `Kapandı` olmamalı.

### Faz 1 Sonunda Beklenen Sonuç

- Operatör aynı iş için iki ekran arasında seçim yapmak zorunda kalmaz.
- "Onaylandı ama aslında bitti mi?" sorusu ortadan kalkar.
- İrsaliye kapanışı operasyon gerçekliğiyle uyumlu hale gelir.

### Kabul Kriterleri

- Normal depocu rolü için inbound tek ana akıştan yürür.
- İrsaliye, tüm yerleştirme görevleri tamamlanmadan kapanamaz.
- Onay ekranından sonra kullanıcıya açık bir sonraki adım gösterilir.

---

## Faz 2 - Mobil Terminal Akışının Endüstri Standardına Getirilmesi ✅ TAMAMLANDI

### Amaç

Terminal ekranını gerçekten saha kullanımına uygun hale getirmek.

### Yapılacaklar

1. Palet doğrulamasını görsel olarak gerçek doğrulama haline getir.
   - Palet okutulunca hemen `Palet tanındı` denmemeli.
   - Doğru mesaj:
   - `Göreve ait palet doğrulandı`
   - Yanlışsa:
   - `Bu barkod bu göreve ait değil. Beklenen palet: ...`

2. Terminal ekranında teknik ID değil operasyonel bilgi göster.

   Görev kartında görünmesi gerekenler:

   - Palet barkodu
   - Ürün adı
   - Lot no
   - Miktar
   - Önerilen raf kodu
   - Zone bilgisi
   - Öncelik

3. Görev ekranında yönlendirme metinlerini sadeleştir.

   Örnek:

   - `Paleti okutun`
   - `Rafı okutun`
   - `Palet başarıyla yerleştirildi`

4. Sonuç ekranında operatöre net kapanış ver.
   - `Sonraki görevi al`
   - `Aynı paletin detayını görüntüle`
   - `Sorun bildir`

5. Terminalde bekleyen görev özetini daha anlamlı hale getir.
   - `Sırada 8 görev var`
   - `2 acil, 3 yüksek öncelikli`

### Faz 2 Sonunda Beklenen Sonuç

- Terminal ilk kez kullanan biri tarafından daha kolay anlaşılır.
- Barkod hataları daha erken yakalanır.
- Operatör ekranı veri tabanı kimlikleriyle değil gerçek saha diliyle kullanır.

### Kabul Kriterleri

- Palet eşleşmesi terminalde anında ve net şekilde doğrulanır.
- Tüm görev ekranlarında palet barkodu ve raf kodu görünür.
- Operatör sonucu aldıktan sonra tek tıkla sonraki göreve geçebilir.

---

## Faz 3 - İstisna Yönetimi ve Hata Dayanıklılığı ✅ TAMAMLANDI

### Amaç

Gerçek depo hayatında sık görülen sapmaları sistem içinde güvenli şekilde yönetmek.

### Yönetilmesi Gereken Temel İstisnalar

1. Eksik ürün
2. Fazla ürün
3. Hasarlı ürün
4. Yanlış ürün
5. Okunamayan barkod
6. Karantina gerektiren ürün
7. Uygun raf bulunamaması
8. Kapasite yetersizliği
9. Zone uyumsuzluğu

### Yapılacaklar

1. Mal kabul ekranına fark/hasar akışı ekle.
   - Kabul tamamlanmadan önce istisna kayıt altına alınabilmeli.

2. Yerleştirme akışında alternatif raf önerisini kullanıcı açısından daha güçlü hale getir.
   - Sadece hata vermek yerine:
   - `Bu raf dolu`
   - `Önerilen alternatifler: A-01, A-03, B-02`

3. Karantina akışını normal yerleştirmeden net biçimde ayır.
   - Kullanıcı hangi durumda karantina başlatacağını net görmeli.

4. Süpervizör override akışını kontrollü hale getir.
   - Gerekçe zorunlu
   - Log zorunlu
   - Sonradan raporlanabilir

5. "İşi bırak / devret / zaman aşımı" akışlarını operasyonel dilde güçlendir.
   - Görev havuza dönünce kullanıcı bunu açıkça görmeli.

### Faz 3 Sonunda Beklenen Sonuç

- Operatör istisna durumunda sistemi dolaşmadan çözüm bulabilir.
- Süpervizör müdahaleleri izlenebilir hale gelir.
- Hata anında süreç kilitlenmez.

### Kabul Kriterleri

- En az 6 temel istisna kullanıcı ekranlarından yönetilebilir.
- Override işlemleri gerekçesiz yapılamaz.
- Alternatif raf önerileri kullanıcıya okunabilir formatta sunulur.

---

## Faz 4 - Operasyon Görünürlüğü ve Süreç Kapanışı ✅ TAMAMLANDI

### Amaç

Sadece işlemi yapmak değil, operasyonu yönetilebilir hale getirmek.

### Yapılacaklar

1. Mal kabul sonrası kısa operasyon özeti üret.
   - Toplam palet
   - Stagingde bekleyen palet
   - Yerleştirilen palet
   - Karantinadaki palet
   - Açık istisna sayısı

2. Süpervizör ekranına inbound kontrol paneli ekle.

   Görünmesi gereken başlıklar:

   - Bugün gelen araçlar
   - Bekleyen kabul
   - Stagingde bekleyen paletler
   - Ortalama yerleştirme süresi
   - En çok hata alınan raflar veya zone'lar

3. İrsaliye detay sayfasına operasyon ilerleme çubuğu ekle.
   - `12 / 12 kabul edildi`
   - `7 / 12 yerleştirildi`
   - `2 istisna açık`

4. Otomatik kapanış ve kapanış sonrası rapor üret.
   - İrsaliye kapandığında küçük bir özet oluşmalı.

### Faz 4 Sonunda Beklenen Sonuç

- Süpervizör süreci telefonla sormadan ekrandan takip eder.
- Açık iş, bitmiş iş ve sorunlu iş ayrışır.
- Sistem operasyonu sadece işler değil, görünür de kılar.

### Kabul Kriterleri

- Her irsaliye için ilerleme yüzdesi görülebilir.
- Süpervizör açık inbound yükünü ekrandan takip edebilir.
- Yerleştirme tamamlanınca kapanış otomatik çalışır.

---

## Faz 5 - Ölçüm, Eğitim ve Sürekli İyileştirme ✅ TAMAMLANDI

### Amaç

Sistemi bir kere düzeltip bırakmak değil, saha verisiyle sürekli iyileştirmek.

### İzlenmesi Gereken KPI'lar

1. Araç kabulden ilk palet girişine geçen süre
2. İlk palet girişinden son palet yerleştirmeye kadar geçen süre
3. Operatör başına saatlik yerleştirme adedi
4. Yanlış palet okutma oranı
5. Yanlış raf okutma oranı
6. Override kullanım oranı
7. Karantina oranı
8. Stagingde 24 saatten fazla bekleyen palet sayısı

### Yapılacaklar

1. Her ana adım için olay kaydı standardı oluştur.
2. Yeni akış için kısa saha eğitim dokümanı hazırla.
3. Terminal ekranı için 3 dakikalık "ilk kullanım" akışı tasarla.
4. İlk yayından sonra saha geri bildirim turu planla.

### Faz 5 Sonunda Beklenen Sonuç

- Geliştirmeler hisle değil veriyle değerlendirilir.
- Eğitim süresi kısalır.
- En çok hata oluşturan noktalar ölçülebilir hale gelir.

---

## Önceliklendirme Özeti

### P0 - Hemen Yapılmalı

1. Normal inbound için tek akış belirlenmesi
2. Manuel `Tamamlandı` kapatmanın kaldırılması
3. Statü modelinin sadeleştirilmesi
4. Onay ve görev oluşturma akışının transaction bütünlüğünün sıkılaştırılması

### P1 - Kısa Vadede Yapılmalı

1. Terminalde palet doğrulama UX iyileştirmesi
2. Terminal görev kartlarının kullanıcı diline çevrilmesi
3. Alternatif raf ve override akışlarının sadeleştirilmesi
4. İstisna yönetimi ekranlarının netleştirilmesi

### P2 - Orta Vadede Yapılmalı

1. Operasyon dashboard'ları
2. KPI takibi
3. Eğitim ve onboarding dokümanları
4. Süreç performans raporları

---

## Ürün Kararı

Bu sistemin başarılı olması için en kritik karar şudur:

**Mal kabul ve yerleştirme birbirine bağlı ama kullanıcı açısından iki ayrı iş değil, tek bir operasyon zinciri gibi tasarlanmalıdır.**

Yani kullanıcı şunu hissetmelidir:

- Mal kabul ettim
- Sistem devamını hazırladı
- Bana sıradaki işi verdi
- Ben de onu bitirdim

Kullanıcı şunu hissetmemelidir:

- Şimdi bunu hangi modülden devam ettireceğim?
- Giriş yaptım mı, onayladım mı, tamamladım mı?
- Bu belge bitti mi, bitmedi mi?

Bu dokümandaki fazlar uygulanırsa sistem sadece çalışan bir depo yazılımı değil, sahada güven veren bir operasyon ürünü haline gelir.

