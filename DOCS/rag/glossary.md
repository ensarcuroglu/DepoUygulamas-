---
id: glossary
audience: operator
aliases:
  - terimler
  - sozluk
  - kavramlar
  - kisaltmalar
related:
  - sistem-genel-bakis
  - fefo-sureci
  - mal-kabul-sureci
  - yerlestirme-putaway-sureci
  - toplama-pick-sureci
  - sevkiyat-sureci
updated: 2026-05-13
verified: true
---

# WMS Terimler Sozlugu

Bu dokuman, depo yonetim sisteminde kullanilan temel terimleri operator gozuyle kisa biçimde aciklar. Asistan, bir terimin tanimi sorulduğunda once buradaki tanima bakmalidir.

## Palet

Palet, depoda urunlerin tasindigi ve depolandigi fiziksel birimdir. Sistemde her paletin bir `palet_no`'su, ic icinde bulundugu lot'u, raf konumu ve `koli_adedi` vardir. Palet kaynagina gore "uretim" veya "tedarikci" olarak ayrilir; uretim paletleri ek bir durum makinesinden gecer (Olusturuldu → KabulBekliyor → KabulEdildi → YerlestirmeBekliyor → Yerlestirildi).

Es anlamli: euro palet, depo paleti.

## Lot

Lot, ayni uretim partisinden gelen ve ayni son kullanma tarihine sahip stok birimidir. Bir lot bir urune baglidir, `lot_no` ve isteğe bagli `parti_no` tasir, `uretim_tarihi` ve `son_kullanma_tarihi` alanlarini icerir. Stok hareketleri, FEFO siralamasi ve raporlama lot bazinda yapilir.

Es anlamli: parti, uretim partisi, batch.

## SKT (Son Kullanma Tarihi)

**SKT ne demek? SKT nedir?** SKT, Son Kullanma Tarihi kisaltmasidir. Bir lottaki urunlerin tuketilebilecegi son tarihi gosterir. FEFO siralamasinin temel kriteridir: SKT'si en yakin uygun stok once cikarilir. SKT'si gecmis lotlar normal sevkiyat icin uygun kabul edilmez; blokaj veya iadeye konu olur. Sistemde `lotlar.son_kullanma_tarihi` alaninda tutulur.

Es anlamli: son kullanma, son kullanma tarihi, expiry, expiration date, mhd, miad.

## FEFO

FEFO (First Expired, First Out), son kullanma tarihi en yakin uygun stokun once kullanilmasi kuralidir. FIFO'dan farklidir: FIFO ilk giren stogu, FEFO ise SKT'si en yakin olan stogu once cikarir. Detay icin FEFO Sureci dokumanina bakin.

Es anlamli: son kullanma onceligi, SKT onceligi.

## FIFO

FIFO (First In, First Out), depoya ilk giren stokun once cikarilmasi kuralidir. SKT bilgisi olmayan urunler veya operasyonel zorunluluklar disinda WMS varsayilan olarak FEFO kullanir.

Es anlamli: ilk giren ilk cikar.

## Raf

Raf, depoda paletin yerlestirildigi fiziksel konumdur. Her rafin bir `kod`u, bagli oldugu `bolge`/`koridor`/`zon` bilgisi ve depo iliskisi vardir. Bazi raflar staging (gecici bekleme) amaclidir; bunlar normal yerlestirme algoritmasinda farkli ele alinir.

Es anlamli: lokasyon, raf konumu.

## Zon

Zon, depo icindeki mantiksal alan bolumlemesidir (ornek: soguk hava zonu, ham madde zonu, sevk zonu). Yerlestirme algoritmasi uygun zonu secerken urun, sicaklik veya kategori kurallarini dikkate alir.

Es anlamli: bolge, alan, zone.

## Depo

Depo, fiziksel olarak ayri tutulan stok lokasyonudur. Bir sirketin birden fazla deposu olabilir; her rafin tek bir deposu vardir ve mal kabul, sevkiyat plani gibi belgelerde depo bilgisi tasinir.

Es anlamli: ambar, warehouse.

## Mal Kabul

Tedarikciden gelen veya uretimden inen urunlerin depoya alinmasi surecinin kisa adidir. Detayli akis, irsaliye durum makinesi, hasarli/eksik palet istisnalari ve onay sonrasi yerlestirme gorev olusumu icin `mal-kabul-sureci` dokumanina bakin.

Es anlamli: kabul, mal giris, giris irsaliyesi.

## Mal Kabul Irsaliyesi

Tedarikciden gelen mali sisteme kaydeden belge. Uc durumdan birinde bulunur: Taslak, Onaylandi, Kapandi. Detayli durum gecisleri ve istisna kurallari icin `mal-kabul-sureci` dokumanina bakin.

Es anlamli: giris irsaliyesi, kabul belgesi.

## Yerlestirme (Putaway)

Mal kabul sonrasi paletin uygun rafa konulma surecinin kisa adidir. Detayli akis, raf onerisi, gorev durum makinesi ve override kurallari icin `yerlestirme-putaway-sureci` dokumanina bakin.

Es anlamli: putaway, raf atama, yerlesim.

## Toplama (Pick / Picking)

Siparis icin paletlerin raftan toplanmasi surecinin kisa adidir. Detayli akis, FEFO onerisi, override kurallari ve gorev durum makinesi icin `toplama-pick-sureci` dokumanina bakin.

Es anlamli: toplama, picking, sevk hazirligi.

## Sevkiyat

Toplanan paletlerin musteriye gonderilme surecinin kisa adidir. Detayli akis, sevkiyat plani durum makinesi, stok hareketi tetiklenmesi ve meta alan kilitleme kurallari icin `sevkiyat-sureci` dokumanina bakin.

Es anlamli: sevk, cikis, gonderim.

## Sevkiyat Plani

Bir siparis icin yukleme detaylarinin tanimlandigi belge: tir plaka, sofor, kapi, yukleme tarihi/saati. Durum ilerledikce alan kilitlenir; YOLDA veya TESLIM_EDILDI durumunda meta alanlar duzenlenemez.

## Stok Hareketi

Sisteme yapilan her stok girisi (`giris`) veya cikisi (`cikis`). Mal kabul, sevkiyat, transfer, iade, sayim duzeltmesi gibi olaylar stok hareketi olarak kaydedilir. Hareketler urun, lot, palet, raf, kullanici, tarih ve baglam (irsaliye_no/siparis_no) tasir.

Es anlamli: hareket, stok kaydi.

## Rezervasyon

Bir paletin bir siparis icin tutulmasi. `Aktif` rezervasyon siparis hazirlanirken olusur; sevkiyat tamamlandiginda `Kesinlesti`, siparis iptal veya palet degisiminde `IptalEdildi` olur. Aktif rezerve palet baska siparise atanamaz.

Es anlamli: palet rezervasyonu, tutma.

## Karantina

Kabul edilmis ancak kalite kontrol bekleyen veya supheli paletlerin tutuldugu durum. `KabulEdildi` durumundaki palet `Karantina`'ya alinabilir; karantinadan cikis yetkili onayi gerektirir. Karantina paletleri normal toplama/sevkiyat icin uygun kabul edilmez.

Es anlamli: karantina alani, kalite bekleme.

## Blokaj / Blokeli Stok

Sevke kapali, hasarli, rezerve veya kalite kontrol bekleyen stok. Blokeli stoklar FEFO siralamasinda ve toplama onerilerinde elenir, raporlarda ayri gosterilir.

Es anlamli: blokeli, sevke kapali, donduruldu.

## Vardiya

Uretim paletlerinde ve operator performans olcumunde kullanilan calisma dilimi (ornek: gunduz, gece, sabah). Palet kayidinda `vardiya` alani tutulur; LMS modulu vardiya bazli KPI hesaplar.

## UPH (Units Per Hour)

**UPH metrigi nedir? UPH ne demek?** UPH, Units Per Hour kisaltmasidir. Operator performans metrigidir: saat basina tamamlanan birim (genelde palet veya koli) sayisini gosterir. LMS (Logistics Management System) modulunde vardiya bazinda hesaplanir ve operator leaderboard'unda gosterilir. Yerlestirme ve toplama gorev tamamlanmalarindan beslenir.

Es anlamli: birim per saat, birim/saat, hourly throughput, saat basi verim.

## Gorev

Operatore atanan is birimi: yerlestirme gorevi veya toplama gorevi. Gorevler havuzdan pull-based cekilir (operator kendine atama yapar). Atama sonrasi belirli sure icinde baslanmazsa timeout uygulanir ve gorev havuza geri doner.

Es anlamli: is emri, task.

## Override

Bir is kuralinin supervisor onayiyla atlanmasi. Yerlestirme'de algoritma onerisi disinda raf, toplama'da FEFO onerisi disinda palet secimi override gerektirir. `override_neden` zorunlu, `override_kullanici_id` supervisor'u tutar.

Es anlamli: yetkili onayi, manuel mudahale.

## Tedarikci

Mal kabul edilen urunun geldigi disardaki firma. Mal kabul irsaliyesinde tedarikci bilgisi tasinir.

Es anlamli: supplier, satici.

## Musteri

Sevkiyat yapilan disardaki firma veya kisi. Siparis ve sevkiyat plani uzerinde musteri adi/adresi tutulur.

Es anlamli: customer, alici.

## Irsaliye

Mal hareketini belgeleyen resmi evrak. Iki tipi vardir: mal kabul irsaliyesi (giris) ve sevkiyat irsaliyesi (cikis). Belge turu, tarih, tir/sofor bilgileri tasir.

Es anlamli: sevk irsaliyesi, irsaliye belgesi.

## Sayim

Stoktaki fiziksel miktarin sistemle karsilastirildigi sureç. Fark cikarsa stok duzeltme hareketi yazilir.

Es anlamli: stock count, envanter sayimi.

## AGV / AMR

Otonom mobil robotlar; bazi yerlestirme veya transfer gorevlerini insan operator yerine yapar. AGV gorev dongusu Bekliyor → Atandi → DevamEdiyor → Tamamlandi seklindedir; AgvSimService uzerinden simule edilir.

Es anlamli: otonom robot, AMR.

## Mobil Terminal

Operatorlerin gorev cekme, barkod okutma ve raf onaylama icin kullandigi mobil cihaz arayuzu (PWA). DepocuLayout veya TerminalLayout uzerinden acilir.

Es anlamli: el terminali, scanner, RF.
