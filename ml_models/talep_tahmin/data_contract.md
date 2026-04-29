# Talep Tahmin Veri Sozlesmesi

Bu dosya, modelin bekledigi minimum input ve urettigi output alanlarini tanimlar.

Bu sozlesme SaaS/B2B urun gelistirme baglaminda musteri verisi henuz yokken
sentetik veri ve acik kaynak veri adapterleriyle de calisabilecek sekilde
tasarlanmistir.

## Input Kaynaklari

Mevcut projedeki dogrulanmis kaynaklar:

- `stok_hareketleri`: Gerceklesmis giris/cikis hareketleri.
- `siparisler`: Siparis basligi, durum ve teslimat tarihi.
- `siparis_kalemleri`: Urun bazli siparis miktari.
- `urunler`: Urun, kategori, marka, tedarikci, minimum stok ve mevcut stok bilgisi.
- `lotlar` ve `paletler`: Aktif stok ve SKT baglami.

`sevkiyat_kalemleri` sadece dikkatli kullanilmalidir; `stok_hareketleri` cikis kayitlariyla birlikte kullanilirsa cift sayim riski dogar.

## Minimum Input Alanlari

| Alan | Tip | Kaynak | Not |
| --- | --- | --- | --- |
| `tenant_id` | str/null | SaaS baglami | Opsiyonel; acik veri ve demo icin `public-demo`/`demo-tenant` olabilir |
| `urun_id` | int | `urunler.id` | Zorunlu |
| `tarih` | date | `stok_hareketleri.tarih` | Gunluk agregasyon icin |
| `gunluk_cikis_miktari` | int/float | `stok_hareketleri.miktar` | `hareket_tipi="cikis"` toplamidir |
| `mevcut_stok` | int/float | `urunler.stok_miktari` | Palet/lot aktif stok toplami |
| `min_stok` | int/float | `urunler.min_stok` | Risk hesabinda kullanilir |

`siparis_miktari`, `kategori_id`, `marka_id`, `tedarikci_id` gibi alanlar sonraki
feature setlerinde kullanilabilir. Ilk baseline sadece stok cikis serisi, mevcut
stok ve minimum stok ile calisir.

## Output Alanlari

| Alan | Tip | Not |
| --- | --- | --- |
| `urun_id` | int | Tahmin yapilan urun |
| `tahmin_gun` | int | 7, 30, 90 gibi ufuk |
| `tahmini_talep` | float | Tahmini toplam talep |
| `gunluk_ortalama_talep` | float | Tahminin gunluk ortalamasi |
| `stok_riski` | str | `yok`, `dikkat`, `kritik` |
| `talep_sinyali` | str | `dusuk`, `normal`, `yuksek` |
| `veri_guven_skoru` | float | 0-1 arasi veri yeterliligi/goreli guven |
| `onerilen_ikmal_miktari` | float | `max(0, tahmini_talep + min_stok - mevcut_stok)` |
| `uyarilar` | list[str] | Veri yetersizligi, oynaklik, stok riski vb. |

## Veri Yoklugu ve Cold-start

Yeni musteri veya yeni urun icin satis/cikis gecmisi olmayabilir. Bu durumda:

- `stok_cikis_gecmisi=[]` kabul edilir.
- `veri_guven_skoru=0` doner.
- tahmin dusuk guvenli cold-start uyarisi tasir.
- musteri verisi olgunlasana kadar sentetik/acik veri sadece demo ve algoritma
  dogrulama amaciyla kullanilir.

## Desteklenen Lokal Veri Kaynaklari

- `SyntheticDemandDataSource`: demo, satis sunumu ve test icin deterministik veri uretir.
- `CsvDemandDataSource`: canonical CSV semasindan model input'u olusturur.
- `PublicDatasetAdapter`: acik kaynak veri kolonlarini canonical semaya map eder.

## Ilk Baseline

Ilk baseline model, ML kutuphanesi gerektirmeden hareketli ortalama ve basit trend katsayisi ile kurulmalidir. Veri yeterliligi kanitlanmadan daha karmasik model uretime baglanmamalidir.
