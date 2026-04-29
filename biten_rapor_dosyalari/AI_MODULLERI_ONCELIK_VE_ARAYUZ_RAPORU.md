# AI Modülleri Öncelik ve Arayüz Yerleşim Raporu

Tarih: 29.04.2026  
Kapsam: Mevcut Depo Yönetim Sistemi için Talep Tahmin, Akıllı Yerleştirme, Doğal Dil ile Sorgulama, Doküman Zekası ve İş Gücü/Operatör Performans modüllerinin geliştirme sırası ve kullanıcı odaklı arayüz yerleşimi.

## Kısa Karar

Modüller tek bir büyük "AI Merkezi" ekranına taşınmamalı. Depo kullanıcıları için en doğru yaklaşım, AI çıktısını kullanıcının zaten karar verdiği ekranda göstermek:

- Depocu: terminalde görev bazlı öneri ve kişisel özet görmeli.
- Lojistik: yerleştirme, inbound, sevkiyat ve raporlama ekranlarında operasyon kararı almalı.
- Admin: KPI, tahmin, ayar, model izleme ve yetki yönetimini görmeli.

Bu nedenle önerilen geliştirme sırası:

1. Akıllı Yerleştirme
2. İş Gücü / Operatör Performans Modülü
3. Doküman Zekası
4. Talep Tahmin
5. Doğal Dil ile Sorgulama

## Mevcut Uygulama Dayanağı

İncelenen mevcut yapı, AI modülleri için iyi bağlanma noktalarına sahip:

- `ReactProje/src/App.jsx`: `inbound-dashboard`, `kpi-dashboard`, `yerlestirme-gorevleri`, `depo-kroki`, `raporlar`, `terminal/ozet`, `siparisler`, `gelen-mal/irsaliyeli` rotaları mevcut.
- `ReactProje/src/components/layout/Sidebar.jsx`: menü grupları zaten operasyon akışına göre ayrılmış: Gelen Mal, Yerleştirme, Toplama, Saha Terminali, Yönetim & Rapor.
- `BackendProje/app/core/services/yerlestirme_algoritmasi.py`: mevcut kural tabanlı yerleştirme skoru var; konsolidasyon, doluluk, FIFO ve zon önceliği kullanılıyor.
- `BackendProje/app/application/use_cases/inbound_kpi_use_cases.py`: operatör verimliliği, yanlış palet okutma, override, karantina ve staging bekleme metrikleri zaten hesaplanıyor.

## Öncelik Tablosu

| Sıra | Modül | Neden Bu Sırada? | Arayüz Yerleşimi | İlk MVP Çıktısı |
|---:|---|---|---|---|
| 1 | Akıllı Yerleştirme | En hızlı değer üretir. Mevcut yerleştirme algoritması ve görev akışı hazır. Staging bekleme, hatalı raf seçimi ve override oranını doğrudan düşürür. | `Yerleştirme > Görev Takibi`, `/terminal/yerlestirme`, `/depo-kroki` | Her palet/görev için önerilen raf, skor, gerekçe, 3 alternatif ve override geri bildirimi. |
| 2 | İş Gücü / Operatör Performans | KPI ve terminal verisi zaten var. Yöneticiye planlama, depocuya kişisel gelişim desteği verir. Operasyonel etkisi yüksek, teknik riski orta-düşük. | `/kpi-dashboard`, `/terminal/ozet`, tercihen yeni `/is-gucu-performans` sekmesi/paneli | Saatlik verim, darboğaz uyarısı, vardiya yük tahmini, kişisel terminal özeti. |
| 3 | Doküman Zekası | Mal kabulde manuel veri girişini azaltır ve veri kalitesini artırır. Sonraki tahmin modüllerinin beslenmesini iyileştirir. OCR/dosya işleme altyapısı gerektiği için 1-2 modülden sonra gelmeli. | `/gelen-mal/irsaliyeli`, `/depocu/kabul/irsaliyeli`, yeni `/dokuman-isleme-kuyrugu` | PDF/fotoğraftan irsaliye alanlarını çıkarma, güven skoru, kullanıcı onay ekranı. |
| 4 | Talep Tahmin | Stratejik değeri yüksek ama güvenilir sonuç için temiz tarihçe gerekir. Sipariş, sevkiyat ve stok hareketi verileri olgunlaştıkça etkisi artar. | Yeni `/talep-tahmin`, `/urunler`, `/siparisler`, `/stok-hareketleri`, `/dashboard` | Ürün/kategori bazlı 7/30/90 günlük tahmin, güven aralığı, kritik stok ve önerilen ikmal uyarıları. |
| 5 | Doğal Dil ile Sorgulama | Kullanımı çekici ama güvenlik, yetki, yanlış cevap ve SQL riski en yüksek modül. Önce metriklerin ve veri sözlüğünün oturması gerekir. | Global üst bar/drawer: "Veriye Sor", `/raporlar` içinde "Doğal Dil ile Rapor", `/dashboard` bağlamsal asistan | Sadece izinli metrikler üzerinde metinden filtreli rapor üretme; cevaplarda kaynak tablo ve filtreleri gösterme. |

## Modül Bazlı Arayüz Önerileri

### 1. Akıllı Yerleştirme

Birincil yer: `Yerleştirme > Görev Takibi` (`/yerlestirme-gorevleri`)

Eklenmesi gereken alanlar:

- Üst özet kartı: "AI Öneri Başarısı", "Override Oranı", "Staging Riskli Palet".
- Görev satırı içinde: önerilen raf, skor, kısa gerekçe, alternatif raflar.
- Detay panelinde: "Neden bu raf?" açıklaması; doluluk, aynı ürün yoğunluğu, FIFO/SKT uyumu, zon uyumluluğu.
- Aksiyonlar: "Öneriyi kabul et", "Alternatif seç", "Override et ve neden gir".

Terminal yerleşimi: `/terminal/yerlestirme`

- Depocuya sade gösterilmeli: "Önerilen Raf: A-01-03", "Alternatif: A-01-04", "Uyarı: soğuk zon dışı raf seçilemez".
- Uzun AI açıklaması terminale konmamalı; terminal hızlı işlem ekranı olarak kalmalı.

Depo kroki yerleşimi: `/depo-kroki`

- Harita katmanı: doluluk + öneri yoğunluğu + sıcak/soğuk bölgeler.
- Raf detayında: "Bu rafa önerilme sebebi" ve "yakında dolacak risk" bilgisi.

### 2. İş Gücü / Operatör Performans

Birincil yer: `/kpi-dashboard`

Başlangıçta yeni sayfa açmak yerine KPI Paneli içinde "İş Gücü" sekmesi daha uygun. Modül büyüyünce `/is-gucu-performans` sayfasına ayrılabilir.

Eklenmesi gereken alanlar:

- Operatör bazlı tamamlanan görev, saatlik hız, hata/override etkisi.
- Vardiya bazlı yük tahmini: "Bugün 14:00-17:00 arası 3 ek operatör gerekebilir".
- Darboğaz kartı: staging, yanlış okutma, uzun görev süresi, yoğun zon.
- Yönetici aksiyonu: görev havuzunu yeniden dengele, yoğun operatöre yeni görev verme, düşük yoğunluklu operatöre atama öner.

Terminal yerleşimi: `/terminal/ozet`

- Sadece kişisel ve yapıcı bilgi gösterilmeli: "Bugün 12 görev tamamlandı", "Ortalama süren son 7 güne göre iyi", "Sıradaki görev önerisi".
- Depocu ekranında rekabetçi/punitif sıralama olmamalı.

### 3. Doküman Zekası

Birincil yer: `/gelen-mal/irsaliyeli` ve `/depocu/kabul/irsaliyeli`

Mevcut "Yeni İrsaliye" akışına "Belgeden İçe Aktar" butonu eklenmeli.

Önerilen kullanıcı akışı:

1. Kullanıcı PDF/fotoğraf yükler.
2. Sistem tedarikçi, tarih, plaka, şoför, palet no, ürün, lot, miktar, SKT alanlarını çıkarır.
3. Kullanıcı belge önizleme ve çıkarılan alanları yan yana görür.
4. Düşük güvenli alanlar sarı işaretlenir.
5. Kullanıcı onaylamadan kayıt oluşmaz.

Yeni yardımcı sayfa: `/dokuman-isleme-kuyrugu`

- Hatalı/düşük güvenli belgeler.
- Bekleyen onaylar.
- İşlenmiş belge geçmişi.
- Admin/lojistik için OCR hata analizi.

### 4. Talep Tahmin

Birincil yeni sayfa: `/talep-tahmin`

Menü önerisi: `Yönetim & Rapor` grubu altında "Talep Tahmin" ya da `Sevkiyat & Dağıtım` altında "Talep Planlama". Kullanıcı açısından en anlaşılır ad "Talep Planlama" olur.

Eklenmesi gereken alanlar:

- Ürün/kategori/müşteri filtreleri.
- 7/30/90 günlük tahmin grafiği.
- Tahmin güven aralığı.
- Gerçekleşen vs tahmin karşılaştırması.
- Önerilen minimum stok güncellemesi.
- Önerilen satın alma/üretim ihtiyacı.

Mevcut sayfalara gömülecek küçük parçalar:

- `/urunler`: ürün detayında "Tahmin" sekmesi.
- `/siparisler`: yeni sipariş girerken "beklenen talep artışı" uyarısı.
- `/stok-hareketleri`: "30 gün içinde kritik seviyeye düşebilir" uyarısı.
- `/dashboard`: "Yaklaşan stok riski" kartı.

İlk sürümde karmaşık model şart değil. Hareketli ortalama, haftalık sezonluk katsayı ve basit trend modeliyle başlayıp tahmin hatası ölçüldükten sonra daha gelişmiş modele geçilmeli.

### 5. Doğal Dil ile Sorgulama

Birincil yer: global üst bar/drawer, ad: "Veriye Sor"

Bu modül ayrı bir sohbet ekranı olarak değil, güvenli rapor/analiz yardımcısı olarak tasarlanmalı.

Önerilen yerleşimler:

- Üst bar: her sayfadan açılan küçük drawer.
- `/raporlar`: "Doğal Dil ile Rapor Oluştur" alanı.
- `/dashboard`: "Bu düşüşün sebebi ne?" gibi bağlamsal analiz önerileri.
- `/inbound-dashboard`: sadece inbound verisiyle sınırlı hızlı sorular.

Güvenlik sınırları:

- Serbest SQL çalıştırmamalı.
- Sadece izinli metrik katalogları üzerinden sorgu üretmeli.
- Cevapta kullanılan filtreleri ve kaynak veri alanlarını göstermeli.
- Yetki rolüne göre kolon/sayfa erişimi uygulanmalı.
- Yazma işlemi yapmamalı; rapor, filtre, özet ve öneri üretmeli.

## Menü ve Sayfa Yapısı Önerisi

Mevcut menü yapısı korunmalı. Yeni modüller için önerilen minimal menü değişikliği:

- `Yerleştirme`
  - Görev Takibi: Akıllı Yerleştirme önerileri burada.
  - Depo Kroki: AI doluluk/öneri katmanı burada.

- `Gelen Mal`
  - İrsaliyeli Kabul: Doküman Zekası burada.
  - Inbound Panel: AI uyarı ve darboğaz önerileri burada.

- `Yönetim & Rapor`
  - Talep Planlama: yeni sayfa.
  - Raporlama Merkezi: Doğal Dil ile Rapor burada.
  - KPI Paneli: İş Gücü sekmesi burada.
  - AI Merkezi: sadece admin ayarları, model durumu, geri bildirim ve hata günlükleri için küçük bir yönetim sayfası.

- `Saha Terminali`
  - Yerleştirme: sadece görev bazlı raf önerisi.
  - Performans Özeti: sadece kişisel özet ve yapıcı öneri.

## Geliştirme Fazları

### Faz 0: AI Altyapı Hazırlığı

Modül geliştirmeden önce ortak altyapı kurulmalı:

- `ai_recommendation_log`: öneri, skor, kullanıcı aksiyonu, override nedeni.
- `ai_feedback`: kullanıcı geri bildirimi.
- Feature flag: AI özellikleri kademeli açılmalı.
- Rol bazlı yetki: admin, lojistik, depocu ayrımı.
- Model/prompt versiyonlama.
- Hata durumunda klasik akışın devam etmesi.

### Faz 1: Operasyonel Quick Win

- Akıllı Yerleştirme önerileri.
- İş Gücü / Operatör Performans paneli.

Bu faz mevcut veriye en yakın ve kullanıcı etkisi en hızlı olan fazdır.

### Faz 2: Veri Kalitesi ve Otomasyon

- Doküman Zekası.
- Mal kabul belge okuma ve insan onaylı kayıt oluşturma.

Bu faz manuel veri girişini azaltır ve sonraki analitik modüllerin kalitesini artırır.

### Faz 3: Planlama Zekası

- Talep Tahmin.
- Stok riski, ikmal önerisi, sevkiyat yoğunluğu tahmini.

Bu faz için yeterli tarihsel veri ve tahmin doğruluğu ölçümü gerekir.

### Faz 4: Doğal Dil Katmanı

- Veriye Sor.
- Doğal dil ile rapor oluşturma.
- Bağlamsal dashboard asistanı.

Bu faz en son gelmeli; çünkü doğru çalışması için veri sözlüğü, metrik katalogları ve rol bazlı güvenlik sınırları oturmuş olmalıdır.

## Sonuç

En doğru strateji, AI modüllerini vitrin olarak değil operasyon karar desteği olarak konumlandırmaktır. Bu uygulamanın mevcut mimarisinde en güçlü başlangıç noktası `Akıllı Yerleştirme`, ardından `İş Gücü / Operatör Performans` modülüdür. Bu iki modül hem mevcut backend/veri yapısına yakın hem de depo kullanıcılarının günlük iş akışında hızlı karşılık bulur.

`Doküman Zekası` üçüncü sırada veri giriş kalitesini yükseltmeli, `Talep Tahmin` dördüncü sırada tarihsel veriye dayalı planlama katmanı olmalı, `Doğal Dil ile Sorgulama` ise en son güvenli raporlama ve analiz asistanı olarak eklenmelidir.
