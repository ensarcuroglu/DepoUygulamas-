# Veritabani Temizlik ve Test Verisi Analiz Raporu

Tarih: 2026-04-21  
Kapsam: `BackendProje` SQLAlchemy modeli, MySQL gelistirme veritabani ve test veri altyapisi  
Inceleme sekli: Salt okunur analiz. Veritabaninda silme, truncate, drop veya insert islemi yapilmadi.

## 1. Yonetici Ozeti

Mevcut sistemin veritabani semasi genel olarak saglam durumda. SQLAlchemy `Base.metadata` ile MySQL `depo_yonetim` semasi arasinda tablo/kolon uyumsuzlugu gorulmedi. Foreign key baglari ve unique kisitlar modelle uyumlu gorunuyor. Yetim foreign key kaydi ve kontrol edilen dogal anahtar alanlarinda tekrar eden deger bulunmadi.

Buna karsin mevcut veri seti temiz, tutarli ve endustri standardinda test verisi olarak kullanilmaya uygun degil. En kritik problem stok ve palet kurgusunda: `paletler` tablosu bos, tum lotlar paletsiz, stok hareketlerinin tamami `cikis` tipinde ve stok hareketlerinin tamaminda `lot_id`, `palet_id`, `raf_id` baglami eksik. Bu durum urun bazinda negatif net stok uretmis durumda.

Onerilen yol: once guvenli bir yedek alinmali, ardindan sadece hedef veritabaninda calisan safety-gate'li bir reset/seed sureci kurulmalidir. Test verileri rastgele degil deterministik, senaryo bazli, tekrar calistirilabilir ve referans/operasyonel veri ayrimi korunarak olusturulmalidir.

## 2. Teknik Zemin

### Veritabani baglantilari

- Gelistirme veritabani: `depo_yonetim`
- Test veritabani: `depo_db_test`
- Motor: MySQL `8.0.45`
- Uygulama baglantisi: `BackendProje/database.py`
- Test izolasyonu: `BackendProje/tests/conftest.py`

### Test altyapisi gozlemi

Test altyapisi dogru yonde kurulmus:

- `.env.test` ayri bir test DB kullaniyor.
- `tests/conftest.py`, DB adinda `test` gecmiyorsa calismayi durduruyor.
- Test session basinda `Base.metadata.drop_all()` ve `create_all()` ile sema sifirlaniyor.
- Her test oncesi tablolara `TRUNCATE` uygulanarak izolasyon saglaniyor.
- API ve integration testlerinde factory-boy factory'leri aktif `db_session` ile baglaniyor.

Risk: Bu yaklasim migration zincirini test etmiyor; test DB dogrudan model metadata'sindan kuruluyor. Sema drift'lerini yakalar, fakat manuel migration scriptlerinin sirali calisip calismadigini garanti etmez.

## 3. Mevcut Sema Durumu

Modelde 31 ana tablo bulunuyor:

`markalar`, `kategoriler`, `depolar`, `zonlar`, `raflar`, `tedarikciler`, `urunler`, `lotlar`, `paletler`, `uretim_seri_sayac`, `palet_durum_log`, `stok_hareketleri`, `sistem_loglari`, `kullanicilar`, `destek_talepleri`, `siparisler`, `siparis_kalemleri`, `sevkiyat_planlari`, `sevkiyat_kalemleri`, `irsaliyeler`, `mal_kabul_irsaliyeleri`, `mal_kabul_kalemleri`, `rapor_sablonlari`, `rapor_loglari`, `rapor_schedules`, `stok_sayimlar`, `stok_sayim_kalemleri`, `yerlestirme_gorevleri`, `toplama_gorevleri`, `palet_rezervasyonlari`, `idempotency_kayitlari`.

Salt okunur karsilastirma sonucunda:

- Eksik tablo: yok.
- Fazla tablo: yok.
- Eksik/fazla kolon: yok.
- Yetim foreign key: yok.
- Kontrol edilen unique/dogal anahtar tekrar grubu: yok.
- Model/DB foreign key ve unique kisit farki: yok.

## 4. Mevcut Veri Snapshot

| Tablo | Kayit |
|---|---:|
| depolar | 3 |
| zonlar | 18 |
| raflar | 12 |
| markalar | 4 |
| kategoriler | 8 |
| tedarikciler | 3 |
| urunler | 4 |
| lotlar | 11 |
| paletler | 0 |
| stok_hareketleri | 9 |
| mal_kabul_irsaliyeleri | 6 |
| mal_kabul_kalemleri | 9 |
| siparisler | 2 |
| siparis_kalemleri | 6 |
| sevkiyat_planlari | 1 |
| sevkiyat_kalemleri | 0 |
| irsaliyeler | 3 |
| yerlestirme_gorevleri | 0 |
| toplama_gorevleri | 0 |
| palet_rezervasyonlari | 0 |
| kullanicilar | 4 |
| sistem_loglari | 395 |

Rol dagilimi dengeli gorunuyor: `admin`, `depocu`, `goruntuleyen`, `lojistik` rollerinden birer kullanici var.

Depo/raf yapisi kismen iyi durumda:

- 3 aktif depo var: `Ana Depo`, `Sevkiyat Deposu`, `DEV-DEPO`.
- 18 zon var; `Genel`, `Karantina`, `MalKabul`, `Sevkiyat`, `Soguk`, `Tehlikeli` tipleri her depoda temsil ediliyor.
- 12 aktif raf var; 3 tanesi staging raf.

## 5. Veri Kalitesi Bulgulari

### Kritik

1. `paletler` tablosu bos.

   Depo uygulamasinin temel stok birimi palet gibi calisiyor. Buna ragmen mevcut DB'de hic palet yok. Bu nedenle palet bazli stok, uretim paleti, yerlestirme, toplama ve rezervasyon akislari dogal veriyle test edilemiyor.

2. Tum lotlar paletsiz.

   `lotlar` tablosunda 11 kayit var, fakat `paletler` bos oldugu icin 11 lotun tamami fiziksel stoktan kopuk.

3. Stok hareketleri negatif net stok uretiyor.

   `stok_hareketleri` tablosunda 9 kaydin tamami `cikis`. Giris hareketi yok. Hesaplanan net stok:

   | Urun | Net stok |
   |---|---:|
   | DEV-001 / DEV Makarna 500g | -115 |
   | DEV-002 / DEV Pirinc 1kg | -115 |
   | DEV-003 / DEV Bulgur 1kg | -65 |
   | DNM-001 / Deneme Urunu | 0 |

4. Stok hareketlerinin tamami operasyonel baglamdan kopuk.

   9 stok hareketinin tamaminda `lot_id`, `palet_id` veya `raf_id` eksik. Bu durum audit, FEFO, palet bazli stok ve raf bazli kapasite testlerini zayiflatir.

### Yuksek

5. Bir urunde master veri eksigi var.

   `DNM-001 / Deneme Urunu` icin `tedarikci_id` bos. Model bunu nullable kabul ediyor, ancak endustri standardi test datasetinde ana urunlerin marka, kategori ve tedarikci baglari dolu olmalidir.

6. Mal kabul verisi tam kapanmis bir akisi temsil etmiyor.

   - `mal_kabul_irsaliyeleri`: 6 kayit.
   - Durumlar: 2 `KAPANDI`, 4 `Onaylandi`.
   - `mal_kabul_kalemleri`: 9 kayit.
   - Kalem durumlari: 8 `GirisYapildi`, 1 `Bekliyor`.
   - 6 mal kabul kaleminde `raf_id` bos.
   - 2 kapali mal kabul irsaliyesinde `kapanma_ozeti` bos.

7. Sevkiyat akisi eksik.

   - 2 siparis ve 6 siparis kalemi var.
   - 1 sevkiyat plani var ama `sevkiyat_kalemleri` bos.
   - `toplama_gorevleri` ve `palet_rezervasyonlari` bos.
   - 3 irsaliyenin 2 tanesinde `sevkiyat_id` bos.

### Orta

8. Lot numaralari ve lot metadatasi deterministik standarda oturmamis.

   Lot adlari karisik:

   - `DEV-LOT-001`, `DEV-LOT-002`, `DEV-LOT-003`
   - `DEV-LOT-015`, `DEV-LOT-016`
   - `LOT-2026-0409-01`, `LOT-2026-638`
   - numeric `0000000000100`
   - bir lotta `lot_no` bos

   Bazi lotlarda `uretim_tarihi` ve `parti_no` bos. FEFO/FIFO ve izlenebilirlik testlerinde bu veri kalitesi yetersiz kalir.

9. Sistem loglari veri setini kirletiyor.

   `sistem_loglari` tablosunda 395 kayit var. Bunun 288'i `Oturum` modulunde. Demo/test verisinde bu kadar log, raporlama ve dashboard testlerini gereksiz gürültüyle etkiler.

10. Seed kaynaklari tutarsiz.

   `BackendProje/seed.py`:

   - Rastgele veri uretiyor.
   - DB'de marka varsa tum seed'i atliyor.
   - Vardiya gibi alanlarda gercekci olmayan degerler var.
   - Test/gelistirme ayrimi ve idempotent temizlik kapsami zayif.

   `BackendProje/dev_seed_minimal.sql` daha iyi bir yonde:

   - Deterministik.
   - DEV namespace kullaniyor.
   - Transaction ve safety gate iceriyor.

   Ancak mevcut DB'de DEV urun/lot izleri kalmis, DEV palet ve DEV stok hareketleri yok. Bu da seed surecinin DB'yi hedeflenen nihai halde tutmadigini veya sonradan operasyonel akislarda bozuldugunu gosteriyor.

## 6. Temizlik Stratejisi

Temizlik iki farkli modda tasarlanmali.

### A. Tam reset modu

Amac: Demo/test icin temiz ve baslangictan tutarli bir DB olusturmak.

Bu mod sadece `depo_yonetim`, `depo_db_test` veya acikca izin verilen lokal veritabanlarinda calismali. Uretim adlari icin kilitlenmelidir.

Onerilen sira:

1. `mysqldump` ile yedek al.
2. Hedef DB adini doğrula.
3. `FOREIGN_KEY_CHECKS=0`.
4. Operasyonel tabloları truncate et.
5. Referans tabloları gerekiyorsa truncate et.
6. `FOREIGN_KEY_CHECKS=1`.
7. Deterministik seed veri setini transaction icinde yukle.
8. Validasyon sorgularini calistir.

Truncate sirasinda modelin `Base.metadata.sorted_tables` sirasinin tersini kullanmak en guvenli yaklasimdir.

### B. Namespace temizligi modu

Amac: Kullanici tarafindan elle girilmis veya korumak istenen veriyi silmeden sadece seed verisini yenilemek.

Kurallar:

- Tum seed verisi `TST-` veya `DEV-` prefix'i tasimali.
- Operasyonel veriler once silinmeli: stok hareketleri, gorevler, rezervasyonlar, paletler, lotlar, siparis/sevkiyat/irsaliye kalemleri.
- Master verilerde sadece seed namespace'i hedeflenmeli.
- Kullanicilar icin sistem rollerini koruyan idempotent upsert kullanilmali.

## 7. Hedef Test Verisi Standardi

Endustri standardina yakin test verisi su katmanlara ayrilmali.

### 1. Referans master veri

- 3 depo:
  - Ana Depo
  - Sevkiyat Deposu
  - Karantina / kalite deposu veya ayni ana depoda karantina zonu
- Her depo icin zonlar:
  - Mal kabul
  - Genel stok
  - Soguk
  - Karantina
  - Sevkiyat
- Raf kod standardi:
  - `GNL-A-01-01-01`
  - `MKB-STG-01`
  - `SVK-DCK-01`
- Her depoda en az 1 staging raf.
- 4 rol:
  - admin
  - depocu
  - lojistik
  - goruntuleyen
- 3 tedarikci.
- 3 marka.
- 5 kategori.
- 8-12 urun; her urunde marka, kategori, tedarikci, barkod, EAN, gramaj, ic_adet, min_stok dolu.

### 2. Inbound / mal kabul senaryolari

Minimum senaryolar:

- Taslak mal kabul irsaliyesi.
- Onaylanmis ama girisi tamamlanmamis mal kabul irsaliyesi.
- Tamamlanmis ve kapanma ozeti dolu mal kabul irsaliyesi.
- Eksik/fazla/hasar istisnasi olan mal kabul kalemi.
- Staging rafta bekleyen palet.
- Yerlestirme bekleyen gorev.
- Tamamlanmis yerlestirme gorevi.

### 3. Stok / palet senaryolari

Minimum senaryolar:

- Aktif palet.
- Karantina paleti.
- Staging paleti.
- Sevkiyata rezerve edilmis palet.
- Pasif/iptal palet.
- Farkli SKT'lere sahip en az 2 lot; FEFO testleri icin.
- Her paletin lot, raf, urun ve miktar baglari tutarli.
- Giris ve cikis stok hareketleri dengeli; net stok negatif olmamali.

### 4. Outbound / sevkiyat senaryolari

Minimum senaryolar:

- Taslak siparis.
- Hazirlaniyor siparis.
- Sevkiyat plani olan siparis.
- Sevkiyat kalemleri dolu plan.
- Aktif palet rezervasyonlari.
- Bekleyen/toplanan/tamamlanan toplama gorevleri.
- Taslak, gonderildi ve teslim edildi irsaliye ornekleri.

### 5. Raporlama ve destek

- 1-2 rapor sablonu.
- 1 zamanlanmis rapor.
- Az sayida sistem logu.
- 2 destek talebi: acik ve kapali.

## 8. Onerilen Validasyon Kapilari

Seed bittikten sonra otomatik olarak su kontroller calismali:

```sql
-- Yetim FK kalmamali.
-- Unique dogal anahtarlarda tekrar olmamali.
-- Aktif paletlerde lot, raf, koli ve kg bilgisi dolu olmali.
-- Net stok negatif olmamali.
-- Her urunun marka/kategori/tedarikci baglari dolu olmali.
-- Her aktif lotun SKT bilgisi dolu olmali.
-- Her sevkiyat planinin en az bir kalemi olmali.
-- Her aktif toplama gorevinin palet/lot/urun/depo baglari tutarli olmali.
```

Onerilen kabul kriterleri:

- `paletler` > 0
- `stok_hareketleri` icinde hem `giris` hem `cikis` bulunur.
- `SUM(giris-cikis)` urun bazinda negatif olmaz.
- `yerlestirme_gorevleri` ve `toplama_gorevleri` icinde en az birer acik ve kapali senaryo bulunur.
- `palet_rezervasyonlari` icinde en az bir `Aktif`, bir `Kesinlesti`, bir `IptalEdildi` kayit bulunur.
- `sistem_loglari` kontrollu sayida tutulur.

## 9. Uygulama Onerisi

Mevcut dosya yapisina en uyumlu cozum:

1. `BackendProje/scripts/` altina yeni bir seed/reset araci eklemek.
2. Araci Python ile yazmak ve SQLAlchemy metadata'sini kullanmak.
3. Modlari ayirmak:
   - `--mode full-reset`
   - `--mode namespace-refresh`
   - `--dry-run`
   - `--yes`
4. Safety gate eklemek:
   - DB adi whitelist icinde olmali.
   - `--yes` olmadan yazma yapmamali.
   - Her calismada once snapshot/backup onerisi veya opsiyonel dump almali.
5. Seed'i deterministik kurmak:
   - Random kullanilacaksa sabit seed ile.
   - Tarihler test icin sabit referans tarihinden turetilmeli.
   - Prefix standardi: `TST-` veya `DEV-`.
6. Son adimda validasyon raporu basmak.

## 10. Karar

Veritabani semasi saglam, fakat mevcut veri seti temiz test verisi degil. En dogru sonraki adim canli gelistirme DB'sinde elle temizlik yapmak degil; safety-gate'li, tekrar calistirilabilir ve validasyonlu bir reset/seed araci olusturmaktir.

Bu arac tamamlandiginda hem `depo_db_test` hem de lokal demo/geliştirme veritabani ayni standarda yakin, tutarli senaryolarla doldurulabilir.
